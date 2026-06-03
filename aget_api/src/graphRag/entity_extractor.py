#This file handles the entitiy extraction from each chunks created using semantic chunking:

from gliner import GLiNER
import re
import json
from typing import List, Sequence, Dict
from langchain_core.documents import Document

import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0" 

class EntityExtractor:
    def __init__(self, labels : List[str] | None, entity_model_name : str = "urchade/gliner_medium-v2.1", threshold : float = 0.4):
        
        if labels is None:
            with open(r"D:\LLM_Deeplearning.ai\AgeT-Agentic-Tutor\aget_api\src\data\entity_labels.json", "r") as f:
                self.labels = json.load(f)
        else:
            self.labels = labels

        self.threshold = threshold
        self.filter = { "exam", "hours", "details", "example", "curve", "study"}

        with open(r"D:\LLM_Deeplearning.ai\AgeT-Agentic-Tutor\aget_api\src\data\entity_normalization.json", "r") as f:
            self.entity_norm = json.load(f)

        self.model = GLiNER.from_pretrained(entity_model_name)


    def extract_equations(self, chunk_text: str) -> list[str]:

        equations = re.findall(r"\$\$(.*?)\$\$",
                                chunk_text,
                                flags=re.DOTALL)

        equations = [eq.strip() for eq in equations if len(eq) > 0]
        return equations
    
    
    def extract_variables(self, equations: str) -> list[str]:

        variables = set()

        pattern = re.compile(r"""
                                \\?[a-zA-Z]+(?:_[a-zA-Z0-9]+)?
                                |
                                [a-zA-Z](?:_[a-zA-Z0-9]+)?
                              """,
                              re.VERBOSE)
        
        for eq in equations:

            matches = pattern.findall(eq)

            for m in matches:

                if len(m) <= 20:
                    variables.add(m)

        return sorted(list(variables))
    

    
    def extract_entities(self, chunk_text: str) -> List[Dict]:

        gliner_pred = self.model.predict_entities(text = chunk_text, 
                                                  labels = self.labels,
                                                  threshold = self.threshold)
        
        entities = []
        entity_covered = set()

        for pred in gliner_pred:

            if pred['text'].lower() in self.filter:
                continue

            entity_key = (pred['text'].lower(), pred['label'])

            if entity_key in entity_covered:
                continue
            else:
                entity_covered.add(entity_key)
                norm_text = self.normalize_entities(entity_text=pred['text'].lower())

                entities.append({
                                "text" : pred['text'].lower(),
                                "normalized_text" : norm_text,
                                "label" : pred['label'],
                                "score" : round(pred['score'],3)
                                }
                                )
            
        return entities
    

    def normalize_entities(self, entity_text: str) -> str:

        entity_text =  entity_text.lower().strip()
        entity_text = re.sub(r"\[\d+\]", "", entity_text)
        entity_text = re.sub(r"[\"'`]", "", entity_text)
        entity_text = re.sub(r"\s+", " ", entity_text)
        entity_text = entity_text.replace('"', "")

        if entity_text in list(self.entity_norm["plural"][0].keys()):
            entity_text = self.entity_norm["plural"][0][entity_text]

        if entity_text in list(self.entity_norm["normalization"][0].keys()):
            entity_text = self.entity_norm["normalization"][0][entity_text]


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
                               "label": "variable",
                               "score": 1.0 
                            })
            

        return { "entities" : entities }
    
