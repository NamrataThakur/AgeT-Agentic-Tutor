#This file handles the relation extraction from each chunks created using semantic chunking:

#This file is not being used in the pipeline as dependency parsing was not performing good enough on scientific and mathematical contents. So moved to LLM based relation extraction with constrained decoding using Pydantic Schema

#Keeping the contents as is for future reference (if needed)

from gliner import GLiNER
import re
import json
import spacy
import itertools
from typing import List, Sequence, Dict
from langchain_core.documents import Document

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graphRag.entity_extractor import EntityExtractor

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0" 


class RelationExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

        #Read this from config file:
        with open(r"D:\LLM_Deeplearning.ai\AgeT-Agentic-Tutor\aget_api\src\data\relation_normalization.json", "r") as f:
            self.relation_patterns = json.load(f)

        #Read this from config file:
        ENTITY_LABELS = ["statistical model", "mathematical function", "optimization method", "statistical test", "loss function",
                    "variable", "parameter", "algorithm", "metric", "statistical concept"]
        self.entity_extractor = EntityExtractor(labels=ENTITY_LABELS, threshold=0.4)
        

    
    def split_sentences(self, chunk_text: str) -> List[str]:

        doc = self.nlp(chunk_text)

        sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 10 ]
        return sentences
    
    
    def extract_local_entities(self, sentences : str, entities: Dict) -> List[Dict]:

        local_entities = []

        sentences = re.sub(r"\[\d+\]", "", sentences)
        print(f"sentences :: {sentences}")
        for entity in entities['entities']:
            #if entity['normalized_text'] in sentences:
            if re.search(r'\b' + re.escape(entity['text']) + r'\b', sentences):
                local_entities.append(entity)

        return local_entities
    

    def extract_dependency_relations(self, chunk_text : str, entities : Dict) -> List[Dict]:

        relations = [] 

        chunk_text = re.sub(r"\[\d+\]", "", chunk_text)
        sentences = self.nlp(chunk_text)

        for sent in sentences.sents:

            for token in sent:

                print(f"Token :: {token}")
                #We are interested to get the dependency parsing results for only for "Verb" tokens:
                if token.pos_ != "VERB":
                    continue

                verb = token.lemma_.lower()

                if verb not in self.relation_patterns:
                    continue
                
                print(f"Verb :: {verb}")
                relation = self.relation_patterns[verb]

                subject , object = None, None

                for tok in token.children:
                    subject_span, object_span = None, None
                    source_entity, target_entity  = None, None

                    print(f"Tok :: {tok.text}, {tok.dep_}, {tok.pos_}")
                    if tok.dep_ in ("nsubj", "nsubpass"):
                        subject = tok

                    elif tok.dep_ in ("dobj", "oprd", "attr"): #, "dative", "oprd"
                        object = tok
                    
                    else:
                        continue

                    print("subj - dep: ", subject)
                    print("object - dep: ", object)

                    if subject and object:
                        subject_span = " ".join([ t.text.lower() for t in subject.subtree])
                        object_span = " ".join([ t.text.lower() for t in object.subtree])
                        print("S Span: ", subject_span)
                        print("O Span: ", object_span)
                        
                    if subject_span:
                        source_entity = self.extract_local_entities(sentences=subject_span, entities=entities)[0]
                        print(f"source_entity :: {source_entity}")

                    if object_span:
                        target_entity = self.extract_local_entities(sentences=object_span, entities=entities)[0]

                    
                    if source_entity and target_entity and source_entity != target_entity:
                        
                        relations.append({
                                            "source" : source_entity['normalized_text'],
                                            "relation" : relation,
                                            "target" : target_entity['normalized_text'],
                                            "sentence" : sent.text.strip(),
                                            "edge_type": "semantic",
                                            "weight": 0.95,
                                        })
                        subject , object = None, None


        return relations
    
    
    def extract_ontology_relations(self, chunk_text : str, entities : Dict) -> List[Dict]:
        BAD_RELATION_WORDS = { "that", "which",  "who"}
        
        relations = []

        chunk_text = re.sub(r"\[\d+\]", "", chunk_text)
        sentences = self.nlp(chunk_text)

        for sent in sentences.sents:

            for token in sent:
                print(f"Token :: {token}, {token.dep_}, {token.lemma_}")
                if token.lemma_ == "be"  : #and token.dep_ in ("ROOT", "advcl")

                    if any(tok.dep_ == "expl" for tok in token.children):
                        continue


                    subject, object = None, None

                    for tok in token.children:

                        subject_span, object_span = None, None
                        source_entity, target_entity  = None, None

                        print(f"Tok :: {tok.text}, {tok.dep_}, {tok.pos_}")
                        if tok.dep_ in ("nsubj", "nsubjpass") and tok.pos_ in ("NOUN", "PROPN") and subject is None:
                            subject = tok

                        elif tok.dep_ in ("attr", "acomp", "oprd") and tok.pos_ in ("NOUN", "PROPN", "ADJ") and object is None:
                            object = tok

                        else:
                            continue

                        print("subj - oct: ", subject)
                        print("object - oct: ", object)

                        if subject and object:
                            # subject_span = " ".join([ t.text.lower() for t in subject.subtree])
                            # object_span = " ".join([ t.text.lower() for t in object.subtree])
                            subject_span = self.extract_compact_noun_phrase(token=subject)
                            object_span = self.extract_compact_noun_phrase(token=object)
                            print("ont - S Span: ", subject_span)
                            print("ont - O Span: ", object_span)
                            

                        if subject_span:    
                            matches = self.extract_local_entities(sentences=subject_span, entities=entities)
                            source_entity = matches[0] if matches else None
                            print(f"oct source entity :: {source_entity}")

                        if object_span:
                            matches = self.extract_local_entities(sentences=object_span, entities=entities)
                            target_entity = matches[0] if matches else None
                            print(f"oct target_entity :: {target_entity}")

                        if source_entity and target_entity and source_entity != target_entity:
                    
                            relations.append({
                                        "source" : source_entity['normalized_text'],
                                        "relation" : "is_a",
                                        "target" : target_entity['normalized_text'],
                                        "sentence" : sent.text.strip(),
                                        "edge_type": "semantic",
                                        "weight": 0.91,
                                    })
                            
                            
                            for child in object.children:
                                print(f"child :: {child.text},  {child.dep_}, {child.pos_}")
                                if child.dep_ in ("conj") and child.pos_ in ("NOUN", "PROPN", "ADJ"):
                                    #conj_phase = " ".join([t.text.lower() for t in child.subtree])
                                    conj_phase = self.extract_compact_noun_phrase(token=child)
                                    print(f"conj_phase :: {conj_phase}")
                                    conj_entity = self.extract_local_entities(sentences=conj_phase, entities=entities)
                                    print(f"conj_entity :: {conj_entity}")

                                    if source_entity and conj_entity and source_entity != conj_entity:
                                        relations.append({
                                        "source" : source_entity['normalized_text'],
                                        "relation" : "is_a",
                                        "target" : conj_entity['normalized_text'],
                                        "sentence" : sent.text.strip(),
                                        "edge_type": "semantic",
                                        "weight": 0.85,
                                    })

                            subject , object = None, None


        return relations
    
    def extract_compact_noun_phrase(self, token):

        words = []

        for left in token.lefts:

            if left.dep_ in ("amod", "compound", "nummod" ):

                words.append(left.text)

        words.append(token.text)

        return " ".join(words)

    def extract_cooccurence_relations(self, chunk_text : str, entities : Dict) -> List[Dict]:

        relations = []

        sentences = self.nlp(chunk_text)

        for sent in sentences.sents:
            unique = set()

            local_entities = self.extract_local_entities(sentences=sent.text.lower(), entities=entities)

            for ent_1, ent_2 in itertools.combinations(local_entities, 2):
                source = ent_1['normalized_text']
                target = ent_2['normalized_text']

                if source == target:
                    continue

                key_pair = tuple(sorted([source, target]))
                if key_pair in unique:
                    continue

                unique.add(key_pair)
                relations.append({
                                    "source" : source,
                                    "relation" : "co_occurs",
                                    "target" : target,
                                    "sentence" : sent.text.strip(),
                                    "edge_type": "contextual",
                                    "weight": 0.2,
                                })

        return relations
    

    def deduplicated_relations(self, relations : List[Dict]) -> List[Dict]:

        unique = {}

        for r in relations:
            key = (r['source'], r['relation'], r['target'])

            if key not in unique:
                unique[key] = r

        
        return list(unique.values())



    def relation_extraction_pipeline(self, entities: Dict, chunk : Document) -> Dict:

        relations = []

        chunk_text = chunk.page_content

        sentences = self.split_sentences(chunk_text=chunk_text)

        dependency_relations = self.extract_dependency_relations(chunk_text=chunk_text, entities=entities)
        print("Dependency Relations Extracted Successfully...!")

        ontology_relations = self.extract_ontology_relations(chunk_text=chunk_text, entities=entities)
        print("Ontology Relations Extracted Successfully...!")

        cooccurence_relations = self.extract_cooccurence_relations(chunk_text=chunk_text, entities=entities)
        print("Co-Occurence Relations Extracted Successfully...!")

        relations = dependency_relations + ontology_relations + cooccurence_relations

        unique_relations = self.deduplicated_relations(relations=relations)
        print("ALL UNIQUE relations Extracted Successfully...!")

        return { "relations" : unique_relations}
    


if __name__ == "__main__":

    rel_obj = RelationExtractor()

    chunk = """In regression analysis, logistic regression[1] (or logit regression) estimates the parameters of a logistic model (the coefficients in the linear or non linear combinations). In binary logistic regression there is a single binary dependent variable, coded by an indicator variable, where the two values are labeled "0" and "1", while the independent variables can each be a binary variable (two classes, coded by an indicator variable) or a continuous variable (any real value)."""

    entities = {'entities': [{'text': 'regression analysis', 'normalized_text': 'regression analysis', 'label': 'statistical test', 'score': 0.494}, {'text': 'logistic regression', 'normalized_text': 'logistic regression', 'label': 'algorithm', 'score': 0.485}, {'text': 'logit regression', 'normalized_text': 'logit regression', 'label': 'algorithm', 'score': 0.454}, {'text': 'parameters', 'normalized_text': 'parameters', 'label': 'parameter', 'score': 0.644}, {'text': 'logistic model', 'normalized_text': 'logistic regression', 'label': 'statistical model', 'score': 0.886}, {'text': 'coefficients', 'normalized_text': 'coefficients', 'label': 'parameter', 'score': 0.601}, {'text': 'dependent variable', 'normalized_text': 'dependent variable', 'label': 'variable', 'score': 0.726}, {'text': 'indicator variable', 'normalized_text': 'indicator variable', 'label': 'variable', 'score': 0.876}, {'text': 'independent variables', 'normalized_text': 'independent variables', 'label': 'variable', 'score': 0.418}, {'text': 'binary variable', 'normalized_text': 'binary variable', 'label': 'variable', 'score': 0.634}, {'text': 'continuous variable', 'normalized_text': 'continuous variable', 'label': 'variable', 'score': 0.676}]}

    dep_relations = rel_obj.extract_dependency_relations(chunk_text=chunk, entities=entities)
    print(dep_relations)

    print('===========================================================')

    oct_relations = rel_obj.extract_ontology_relations(chunk_text=chunk, entities=entities)
    print(oct_relations)
                
        
    
        