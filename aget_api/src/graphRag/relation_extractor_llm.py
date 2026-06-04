#This file handles the relation extraction from each chunks created using semantic chunking:

from gliner import GLiNER
import re
import json
import spacy
import itertools
from typing import List, Sequence, Dict
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from pydantic_models.models import RelationExtractBatch, RELATION_TYPES
from graphRag.prompts import RELATION_EXTRACTION_PROMPT

openai_api_key = os.getenv("OPENAI_API_KEY")


class RelationExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.llm = ChatOpenAI(name="gpt-4.1-mini", temperature=0.00, api_key=openai_api_key, max_tokens=1200, max_retries=3)

        #Read this from config file:
        with open(r"D:\LLM_Deeplearning.ai\AgeT-Agentic-Tutor\aget_api\src\data\relation_normalization.json", "r") as f:
            self.relation_patterns = json.load(f)

    
    def split_sentences(self, chunk_text: str) -> List[str]:

        doc = self.nlp(chunk_text)

        sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 10 ]
        return sentences
    
    
    def extract_local_entities(self, sentences : str, entities: Dict) -> List[Dict]:

        local_entities = []

        sentences = re.sub(r"\[\d+\]", "", sentences)

        for entity in entities['entities']:
            #if entity['normalized_text'] in sentences:
            if re.search(r'\b' + re.escape(entity['text']) + r'\b', sentences):
                local_entities.append(entity)

        return local_entities
    

    def validate_relations(self, relations : List[Dict], entities : Dict) -> List[Dict]:
        valid_relations = []

        entity_set = set([entity['normalized_text'] for entity in entities['entities']])

        for rel in relations:
            if rel['source'] in entity_set and rel['target'] in entity_set and rel['source'] != rel['target']:
                valid_relations.append(rel)
        
        return valid_relations
    

    def canonicalize_relations(self, relations : List[Dict]) -> List[Dict]:
        
        standardized_relations = []

        for rel in relations:
            rel = rel.copy()
            relation = rel['relation']

            stan_rel = self.relation_patterns.get(relation,relation)
            rel['relation'] = stan_rel
            standardized_relations.append(rel)

        return standardized_relations
    

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
                                    "explanation" : sent.text.strip(),
                                    "edge_type": "contextual",
                                    "weight": 0.2,
                                })

        return relations
    

    def prune_relations(self, relations : List[Dict]) -> List[Dict]:

        pruned_relations = []
        semantic_entity_pair = set()

        for rel in relations:
            if rel['edge_type'] == 'semantic':
                semantic_entity_pair.add((rel['source'], rel['target']))
                pruned_relations.append(rel)
        
        for rel in relations:
            if rel['edge_type'] == "contextual":
                entity_pair = (rel['source'], rel['target'])
                reverse_pair = (rel['target'], rel['source'])
                if entity_pair not in semantic_entity_pair and reverse_pair not in semantic_entity_pair:
                    pruned_relations.append(rel)

        return pruned_relations
    
    def deduplicated_relations(self, relations : List[Dict]) -> List[Dict]:

        unique = {}

        for r in relations:
            key = (r['source'], r['relation'], r['target'])

            if key not in unique:
                unique[key] = r

        
        return list(unique.values())
    
    def relation_extraction_pipeline(self, entities: Dict, chunk : Document) -> Dict:
        
        print("Relation Extraction Pipeline Started..!")
        chunk_text = chunk.page_content
        relation_extraction_prompt = PromptTemplate(template=RELATION_EXTRACTION_PROMPT,
                                                    input_variables=["relation_types","entity_list","chunk"],
                                                    )
        
        structured_llm = self.llm.with_structured_output(RelationExtractBatch)

        relation_chain = relation_extraction_prompt | structured_llm

        relation = relation_chain.invoke({"relation_types": RELATION_TYPES, 
                                          "entity_list":entities['entities'],
                                           "chunk": chunk_text, 
                                          })
        print("Relations Extracted Successfully Using LLM ...!")

        llm_relation = []
        for rel in relation.relation:
            obj = {
                "source" : rel.source,
                "relation" : rel.relation,
                "target" : rel.target,
                "explanation" : rel.explanation,
                "edge_type" : rel.edge_type,
                "weight" : rel.confidence
            }
            llm_relation.append(obj)

        cooccurence_relations = self.extract_cooccurence_relations(chunk_text=chunk_text, entities=entities)
        print("Co-Occurence Relations Extracted Successfully...!")

        print("Relation Post-Processing Started..!")
        relations = llm_relation + cooccurence_relations

        unique_relations = self.deduplicated_relations(relations=relations)
        print("ALL UNIQUE relations Extracted Successfully...!")

        valid_relations = self.validate_relations(relations=unique_relations, entities=entities)
        print("Relations Validated Successfully...!")

        standardized_relations = self.canonicalize_relations(relations=valid_relations)
        print("Relations Standardized Successfully...!")

        final_relations = self.prune_relations(relations=standardized_relations)
        print("Redundant Relations Pruned Successfully...!")
        print("------------------------------------------------------------------------")
        return final_relations