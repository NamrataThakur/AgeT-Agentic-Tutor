#This file handles the entitiy extraction from each chunks created using semantic chunking:

from gliner import GLiNER
import re
import json
from typing import List, Sequence, Dict
from langchain_core.documents import Document

import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0" 

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config.settings import settings

class EntityExtractor:
    def __init__(self, labels : List[str] | None, entity_model_name = settings.MODEL_NAME_ENTITY_EXTRACTION, 
                    threshold = settings.ENTITY_THRESHOLD):
        
        if labels is None:
            with open(settings.ENTITY_LABELS_JSON_PATH, "r") as f: # TO DO
                self.labels = json.load(f)
        else:
            self.labels = labels

        self.threshold = threshold
        self.filter = { "exam", "hours", "details", "example", "curve", "study",  "age", "sex", "income", "race", "customer",
                        "patient", "homeowner", "voter", "trauma and injury severity score", "triss"}

        with open(settings.ENTITY_NORMALIZATION_JSON_PATH, "r") as f:
            self.entity_norm = json.load(f)

        self.model = GLiNER.from_pretrained(entity_model_name)


    def extract_equations(self, chunk_text: str) -> list[str]:

        equations = []

        #Extract equations from chunk:
        equations.extend(re.findall(r"\$\$(.*?)\$\$",
                                chunk_text,
                                flags=re.DOTALL))
        equations.extend(
            re.findall(r"\$(.*?)\$", chunk_text, flags=re.DOTALL)
        )

        equations.extend(
            re.findall(r"\\\[(.*?)\\\]", chunk_text, flags=re.DOTALL)
        )

        equations.extend(
            re.findall(r"\\\((.*?)\\\)", chunk_text, flags=re.DOTALL)
        )

        #Normalize equations:
        # 1: Remove latex symbols:
        #equations = [re.sub(r"\\[a-zA-Z]+", "", eq) for eq in equations]
        # 2: Keep non-empty equations:
        equations = [eq.strip() for eq in equations if len(eq) > 0]
        equations = [re.sub(r"\s+", "", eq) for eq in equations if len(eq) > 0]

        #Remove index equations
        equations = [eq for eq in equations if not self.is_index_equation(equation=eq)]

        #Keep sufficiently complex equations having score more than 3:
        equations = [eq for eq in equations if self.equation_complexity(eq) >= 3]

        equations = self.normalize_equations(equations=equations)
        return equations
    

    def normalize_equations(self, equations : str):

        normalized_equations = []

        for eq in equations:

            for k, v in self.entity_norm["LATEX_MAP"].items():
                eq = eq.replace(k, v)

            normalized_equations.append(eq)

        return normalized_equations

    def is_index_equation(self, equation : str):

        return bool(
            re.fullmatch(
                r"[ijkmn]\s*=+\s*[A-Za-z0-9]+\s*=+\s*[A-Za-z0-9]+",
                equation.strip()
            )
        )
    

    def equation_complexity(self, equation: str) -> int:

        score = 0

        operators = r"[+\-=*/^|()]"
        score += len(re.findall(operators, equation))

        variables = re.findall(r"[a-zA-Zβσπθ]+", equation)
        score += len(set(variables))

        return score


    def extract_variables(self, equations: list[str]) -> list[str]:
        """
        Extract meaningful mathematical variables/parameters from equations.

        Keeps:
            β_0, β_1, μ, σ, θ, s

        Drops:
            x, y, p, i, j, k, n
            frac, left, right, text
            equation artifacts
        """

        variables = set()        

        pattern = re.compile(
            r"""
            \\beta(?:_\{?\d+\}?)?
            |
            \\mu(?:_\{?\d+\}?)?
            |
            \\sigma(?:_\{?\d+\}?)?
            |
            \\theta(?:_\{?\d+\}?)?
            |
            \\pi
            |
            [βμσθπ]
            |
            [a-zA-Z](?:_\{?\d+\}?)?
            """,
            re.VERBOSE
        )

        for eq in equations:

            # Remove latex commands
            eq = re.sub(r"\\[a-zA-Z]+", "", eq)

            matches = pattern.findall(eq)

            for var in matches:

                var = var.strip()

                if not var:
                    continue

                # Drop placeholder variables
                if var.lower() in set(self.entity_norm["placeholder_variables"]):
                    continue

                # Drop latex commands
                if var.lower() in set(self.entity_norm["latex_commands"]):
                    continue

                # Drop very long garbage strings
                if len(var) > 20:
                    continue

                variables.add(var)

        return sorted(list(variables))
    


    def filter_math_entities(self, entity_text: str) -> int:

        entity_text = entity_text.strip()

        # Remove p, x, y, p_k, p_{k}
        if re.fullmatch(
            r"[pqxyztijkmn](?:_\{?[a-zA-Z0-9]+\}?)?",
            entity_text
        ):
            return 0

        return 1
    
    def extract_entities(self, chunk_text: str) -> List[Dict]:
        
        #Remove the reference number from text like [1], [20] etc. These reference numbers are very common in scientific literature.
        chunk_text = re.sub(r"\\[\d+\\]", "", chunk_text)

        gliner_pred = self.model.predict_entities(text = chunk_text, 
                                                  labels = self.labels,
                                                  threshold = self.threshold)
        
        entities = []
        entity_covered = set()

        for pred in gliner_pred:

            raw_text = pred["text"].lower().strip()

            if raw_text in self.filter:
                continue

            if self.filter_math_entities(entity_text=raw_text):

                if len(raw_text) == 1 and pred["label"] in {"hyperparameter","parameter","optimization_parameter"}:
                    ent_text = self.normalize_hyperparam_entities(entity=raw_text)

                else:
                    ent_text = raw_text

                norm_text = self.normalize_entities(entity_text=ent_text)

                if norm_text == "":
                    continue


                entity_key = (norm_text) #, pred['label']

                if entity_key in entity_covered:
                    continue
                else:
                    entity_covered.add(entity_key)
                    
                    entities.append({
                                    "text" : ent_text,
                                    "normalized_text" : norm_text,
                                    "label" : pred['label'],
                                    "score" : round(pred['score'],3)
                                    }
                                    )
            
        return entities
    
    def normalize_hyperparam_entities(self, entity : str) -> str:

        symbol_map = {
            "a": "alpha",
            "α": "alpha",
            "b": "beta",
            "β": "beta",
            "g": "gamma",
            "γ": "gamma",
            "l": "lambda",
            "λ": "lambda",
            "μ": "mu"
        }

        return symbol_map.get(entity, entity)
    


    def normalize_entities(self, entity_text: str) -> str:

        entity_text =  entity_text.lower().strip()
        entity_text = re.sub(r"\[\d+\]", "", entity_text)
        entity_text = re.sub(r"[\"'`]", "", entity_text)
        entity_text = re.sub(r"\s+", " ", entity_text)
        entity_text = entity_text.replace('"', "")

        if entity_text in set(list(self.entity_norm["plural"][0].keys())):
            entity_text = self.entity_norm["plural"][0][entity_text]

        if entity_text in set(list(self.entity_norm["normalization"][0].keys())):
            entity_text = self.entity_norm["normalization"][0][entity_text]

        ent = entity_text.split()
        if len(ent) > 3 or any(word in set(self.entity_norm['entity_stopwords']) for word in ent) :
            entity_text = ""

        return entity_text
    
    
    def entity_extraction_pipeline(self, chunk : Document) -> Dict:

        print("Entity Extraction Pipeline Started ...!")

        chunk_text = chunk.page_content

        equations = self.extract_equations(chunk_text=chunk_text)
        print("Equations Extracted Successfully...!")

        variables = self.extract_variables(equations=equations)
        print("Variables Extracted Successfully...!")

        entities = self.extract_entities(chunk_text=chunk_text)
        print("Entities Extracted Successfully...!")
        

        for eq in equations:
            entities.append({
                            "text" : eq,
                            "normalized_text" : eq,
                            "label" : "equation",
                            "score": 1.0
                            })
            
        for var in variables:
            entities.append({
                               "text": var,
                               "normalized_text" : var,
                               "label": "parameter",
                               "score": 1.0 
                            })
            

        return { "entities" : entities }
    
