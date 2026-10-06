#This file handles the relation extraction from each chunks created using semantic chunking:

import warnings

warnings.filterwarnings("ignore")

from gliner import GLiNER
import re
import json
import spacy
import itertools
from typing import List, Sequence, Dict
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from sklearn.metrics.pairwise import cosine_similarity
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

from data_models.models import RelationExtractBatch, RelationType, GraphRelationBatch, OntologyMapping
from prompts.relation_extraction_prompt import RELATION_EXTRACTION_PROMPT
from prompts.graph_relation_mapping_prompt import GRAPH_RELATION_MAPPING_PROMPT
from embeddings.embedders import EmbeddingsCreator
from config.settings import settings

openai_api_key = os.getenv("OPENAI_API_KEY")
ALLOWED_RELATIONS = [ r.value for r in RelationType]
ENTITY_SIM_THRESHOLD = 0.5


class RelationExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.embedders = EmbeddingsCreator(embed_model_type=settings.MODEL_TYPE)
        self.llm = ChatOpenAI(name=settings.MODEL_NAME, 
                              temperature=settings.MODEL_TEMPERATURE, 
                              api_key=openai_api_key, 
                              max_tokens=settings.MAX_TOKENS_REL_EXTRACTION,
                              max_retries=settings.MAX_RETRIES)

        #Read this from config file:
        with open(settings.RELATION_NORMALIZATION_JSON_PATH, "r") as f:
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
                                    "weight": 0.3,
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
            if rel['edge_type'] == "contextual" or rel['edge_type'] == "conceptual":
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
    

    def extract_llm_raw_relations(self, entities : Dict, chunk_text : str) -> RelationExtractBatch:

        relation_extraction_prompt = PromptTemplate(template=RELATION_EXTRACTION_PROMPT,
                                                    input_variables=["entity_list","chunk"],
                                                    )
        
        structured_llm = self.llm.with_structured_output(RelationExtractBatch)

        relation_chain = relation_extraction_prompt | structured_llm

        raw_relation = relation_chain.invoke({"entity_list":entities['entities'],
                                                "chunk": chunk_text, 
                                            })
        print("Raw form Relations Extracted Successfully Using LLM ...!")

        return raw_relation
    

    def canonicalize_llm_relations(self, source : str, raw_relations : str, target : str) -> RelationType:

        raw_relations = raw_relations.strip().lower()
        if raw_relations in self.relation_patterns:
            return self.relation_patterns[raw_relations]
        
        relation = self.classify_relation(source = source, raw_relations = raw_relations , target = target)

        return relation
    

    def classify_relation(self, source : str, raw_relations : str, target : str) -> RelationType:

        relation_extraction_prompt = PromptTemplate(template=GRAPH_RELATION_MAPPING_PROMPT,
                                                    input_variables=["source","raw_relation", "target", "ALLOWED_RELATIONS"],
                                                    )
        
        structured_llm = self.llm.with_structured_output(OntologyMapping)

        relation_chain = relation_extraction_prompt | structured_llm

        ontology_relation = relation_chain.invoke({"source":source,
                                                "target": target, 
                                                "raw_relation": raw_relations, 
                                                "ALLOWED_RELATIONS": ALLOWED_RELATIONS, 
                                            })
        
        return ontology_relation.ontology_relation

    def build_graph_relations(self, raw_relation : RelationExtractBatch) -> list[Dict]:

        final_ontology_relations = []

        for rel in raw_relation.relation:
            ontology_relations = self.canonicalize_llm_relations(source=rel.source,
                                                                 raw_relations=rel.relation,
                                                                 target=rel.target)
            
            obj = {
                "source" : rel.source,
                "relation" : ontology_relations,
                "target" : rel.target,
                "explanation" : rel.explanation,
                "edge_type" : rel.edge_type,
                "weight" : rel.confidence
            }

            final_ontology_relations.append(obj)
        
        print("Ontology Relations Mapped Successfully Using LLM ...!")    
        return final_ontology_relations
    

    def build_chunk_entity_relations(self, entities: Dict, chunk_id : str) -> List[Dict]:
        mentions = []

        for entity in entities:
            obj = {
                "source" : chunk_id,
                "relation" : "mentions",
                "target" : entity['normalized_text'],
                "explanation" : "Entity present in the chunk",
                "edge_type" : "mentions",
                "weight" : 0.2
            }

            mentions.append(obj)

        return mentions
    

    def build_similar_entity_relations(self, entities: Dict, chunk_text : str) -> List[Dict]:
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

                #Get the entity embeddings:
                source_embeddings = self.embedders.get_query_embeddings(query = source)
                target_embeddings = self.embedders.get_query_embeddings(query = target)

                cos_sim = cosine_similarity(X=[source_embeddings], Y=[target_embeddings])[0][0]

                if cos_sim >= ENTITY_SIM_THRESHOLD:

                    relations.append({
                                        "source" : source,
                                        "relation" : "conceptually_similar",
                                        "target" : target,
                                        "explanation" : sent.text.strip(),
                                        "edge_type": "conceptual",
                                        "weight": float(cos_sim),
                                    })

        return relations
    
    def relation_extraction_pipeline(self, entities: Dict, chunk : Document, chunk_id : str) -> Dict:
        
        print("Relation Extraction Pipeline Started..!")
        chunk_text = chunk.page_content
        
        raw_relation = self.extract_llm_raw_relations(entities=entities, chunk_text=chunk_text)
        ontology_relations = self.build_graph_relations(raw_relation=raw_relation)

        cooccurence_relations = self.extract_cooccurence_relations(chunk_text=chunk_text, entities=entities)
        print("Co-Occurence Relations Extracted Successfully...!")

        mentions_relations = self.build_chunk_entity_relations(entities=entities, chunk_id=chunk_id)
        print("Chunk-Entity 'Mentions' Relations Extracted Successfully...!")

        conceptual_relations = self.build_similar_entity_relations(entities=entities, chunk_text=chunk_text)
        print("Conceptual Relations Extracted Successfully...!")

        print("Relation Post-Processing Started..!")
        relations = ontology_relations + cooccurence_relations + mentions_relations + conceptual_relations

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