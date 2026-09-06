# Knowledge Capabilities

> Inventory of all capabilities currently implemented in the AgeT knowledge subsystem.
>
> **Purpose**
> - Reconstruct the existing knowledge architecture.
> - Identify all capabilities currently available.
> - Identify current callers and dependencies.
> - Determine which capabilities should be exposed through Knowledge MCP.
> - Avoid rewriting existing knowledge functionality during MCP integration.
>
> **Status:** Working Inventory  
> **Last Updated:** 2026-09-05

---

## Major Components

| Component | Responsibility | Location |
|---|---|---|
| GraphRAG | | |
| Knowledge Store | | |
| Knowledge Retrieval | | |
| Question Generation | | |
| Question Validation | | |
| QS Bank | | |
| Buckets | | |
| Hashing | | |
| Persistence | | |


---



## 1. Knowledge Subsystem Overview

## Purpose

The knowledge subsystem is responsible for creating the knowledge base that powers AgeT's entire agentic capabilities. This sub-system covers everything from extracting contents from Wikipedia for a particular topic to generating the topic specific final question bank that will be used during the on-line interview sessions. It is built in a modular fashion in such a way that we can add a Document Intelligence MCP service that can read the uploaded pdf and run a two-stage OCR pipeline to give the entire content in a markdown format. The remaining modules can then pick up this markdown file and continue with the downstream tasks like semantic chunking, embedding creation etc.

Currently, the knowledge system only allows content extraction from Wikipedia sources. The Document Intelligence MCP service is being built separately and is not integrated with AgeT's interview system or the knowledge sub-system.

## High-Level Flow

Knowledge Sub-system has **three** distinct flows: </br>
A) Create the knowledge base </br>
B) Hybrid GraphRAG to retrieve information from the knowledge base </br>
C) Question generation using the retrieved context


### 1: Knowledge Base</br>

**Flow for creating the knowledge base:**</br>

**Step 1:**</br>
 Read the topic id and list of urls (from which we want to ingest content) from the `data.json` file and populate them into a Pydantic object for structure processing.

**Step 2:**</br>
 Use the `TopicFactory` class to create another Pydantic object called `Topic` for each topic containing fields like `id`, `name` and `tags`. `id` is used for all the remaining downstream tasks like graphRag etc. `name` contains natural langugage text corresponding to the `id`. `tags` contains all the relevant technical keywords that are associated with the topic. 

```text
Example:

id   = "ann"
name = "Artificial Neural Network"
tags = [
    "supervised",
    "regression",
    "nn",
    "neural network",
    "ann",
    "mlp",
    "multi layer perceptron"
]
```

`tags` are specificially helpful for topic detection from user input in the form of speech or text. 

**Step 3: Information Extraction Stage:**</br>
 The Pydantic object `Topic` and the urls will then be passed onto the Information Extraction Stage. It uses WebBaseLoader to extract content from the url. Then, it uses BeautifulSoup to parse the HTML content to extract the text and the equations in the form of LaTeX. It wraps the equations within a `"$$...$$"` to extract the equations in the later stages. As a final step, it assigns the clean text to the page_content attribute of the LangChain's Document class. It also adds the topic id and topic name to the metadata attribute of Document class. 

Output is thus a list of Documents, each containing the parsed and cleaned text along with equations and topic details.


**Step 4: Creation of Semantic Chunks:**</br>
 We used LangChain's `SemanticChunker` as the text-splitter with OpenAI's `text-embedding-3-large` model and `90 percentile` breakpoint threshold with `minimum chunk size as 400`. We use semantic chunker because the techincal information pertaining to a certain concept (for example: sigmoid) may flow across couple of sentences or an entire paragraph. Splitting the text at arbitrary point will run the risk of separating semantically related information out or putting information across different un-related concepts in one chunk. Thus, semantic chunking provided a better local unit of information for the downstream retrieval and knowledge extraction pipeline.


**Step 5: Creating text based embeddings:**</br>
 We use OpenAI's `text-embedding-3-large` model to create embeddings for each chunk text. These embeddings along with the chunk text will later be stored in the MongoDB collection.


**Step 6: Chunk-wise Entity Extraction Stage:**</br>
 We pass the chunk-wise Document object to the Entity Extraction Pipeline. This pipeline extracts `3` types of entities: `equations`, `variables` and `entity`.
 Each of these extractions includes multiple steps. 

 The rules to follow for equation, variables and entity normalization and cleaning as present in the `entity_normalization.json` file under the folder `data`.

 **a) Equations:**</br>
- Extract the equation present within the `"$$...$$"` enclosure present in the chunk text.
- Check if the extraction equation portion is non-empty, remove those if true
- Remove the equation extracted if it is an index equation. `Ex: i=1` These would not add any importance as graph node
- Check the complexity of the equation extracted. Complexity is computed by the presence of operators like `+\-=*/^|()` and mathematical symbols like `a-zA-Zβσπθ`. For every occurence of operator or symbol, the complexity count is increased by 1. Only equations with `complexity >= 3` are kept in the final equation list.
- Finally, normalize the equation list. 
With this, we have the final equations saved in the entity list with label as `equation` and score as `1.0`.

```text
Example :
    text : "y=beta_{0}+beta_{1}x"
    normalized_text : "y=beta_{0}+beta_{1}x"
    label : "equation"
    score : 1
```
**b) Variables:**</br>
- Extract meaningful mathematical variables/parameters from equations extracted in the above step.
- Keeps:  β_0, β_1, μ, σ, θ, s, c, u
- Drops placeholder variables and latex commands in the text:
        x, y, p, i, j, k, n,
        p_k, p_{k}
        frac, left, right, text
        equation artifacts
- Drop very long garbage strings having length more than 20. 
With this, we have the final parameters saved in the entity list with label as `parameter` and score as `1.0`.

```text
Example :
    text : "c"
    normalized_text : "c"
    label : "parameter"
    score : 1
```

**c) GliNER Entities:**</br>
- Peform a basic text cleaning on the chunk text.
- We use an entity extractor model from GliNER family of models called `urchade/gliner_medium-v2.1` with a similarity threshold of `0.4`.
- We also need to pass of labels as a zero-shot technique to guide the model to extract entities pertaining to these specific labels only. The label list is present in `entity_labels.json` file under the same `data` folder. This label list might need to expand as and when we include more topics in the application. For the current topic (logistic regression), a snapshot of label list : 
```text
["statistical concept", "statistical unit", "mathematical concept", "probability concept", "optimization concept", "machine learning concept", "statistical model"...]
```
- We apply an additional filter on the output of GliNER prediction to remove words belonging to particular example usecases. These words can be predicted as possible entities by the model and it depends entirely on the source material. If the material changes or a new topic is introduced, some additional effort will be required to come to the final filter list.
```text
    Example: "example", "curve", "study",  "age", "sex", "income", "race", "customer", "patient", "homeowner", "voter"...
```
- We perform a normalization procedure to replace mathematical notations with their equivalent text. 
```text
    Example: "β": "beta", "a": "alpha" etc
```
- We also perform textual normalization process to standardise the entity names. In this step, we convert plurals to singular, remove stopwords from the entity phase predicted like "approximately", "ranging" etc and convert several forms of the same entity to one constant form.
```text
    Example :  "mle": "maximum likelihood estimation",
               "maximum-likelihood estimation": "maximum likelihood estimation",
               "chi square": "chi-square",
               "chisquare": "chi-square",
               "independent variables": "independent variable",
               "probabilities" : "probability",
            etc
```
- As a final step, we perform de-duplication to keep only unique entities for a chunk.

With this, we have the final entites saved in the entity list with label and score as predicted by the GliNER model.

```text
Example :
    text : "linear regression"
    normalized_text : "linear regression"
    label : "statistical model"
    score : 0.457 
```

With this we finish the Chunk-wise Entity Extraction Stage.


**Step 7: Chunk-wise Relation Extraction Stage:**</br>
- We use the entity extracted from the above step, chunk text and chunk id (which is an unique UUID generated for each chunk) to the Relation Extraction Pipeline. This pipeline extracts `4` types of relations: `semantic`, `contextual`,  `conceptual` and `mentions`.
 Each of these extractions includes multiple steps. 

 The rules to follow for relation standardisation and cleaning as present in the `relation_normalization.json` file under the folder `data`.
 
 We extract relations between a pair of entities existing in a particular chunk text. Entity and Relation extraction thus works at a chunk level and not on the overall document.

 **a) Semantic Relations:**</br>

During initial prototyping, we implemented a strict, single-pass structured extraction schema (Pydantic via JSON mode). However, we observed a high rate of context loss. The LLM would either hallucinate semantic variants of our Enums (e.g., generating minimises instead of minimize) causing strict validation to drop the edge entirely, or it would omit novel relationships not yet captured by our strict ontology. 

To solve this, we designed a `Two-Stage Ingestion Pipeline` for capturing the semantic relations:
- **Discovery Phase:** A unconstrained, zero-shot extraction layer optimized for maximum recall, capturing raw mathematical expressions and free-form semantic verbs directly from the chunk text.
- **Alignment Phase:** A specialized classification pass that maps the open-world verbs into our closed-world graph schema. This separation of concerns guarantees we never drop a chunk due to schema mismatches, while maintaining an immutable, valid graph topology downstream.

Semantic Relations are the most important type of relations as the define rich mathematical association between a pair of entities. The allowed associations are pre-defined in an Enum class called `RelationType` present in the `models.py` file in the `data_models` folder. We want to make sure the set of relations remain semantically relevant and mathematically meaningful so that we can create a enriched entity-relation knowledge graph. 
```text
    Example of allowed relations: 
    generalizes, predicts, optimizes, parameter_of, depends_on, derived_from, instance_of, is_a, converts, maps_to, defined_as, represented_as ...
```
    
- Stage 1: We use LLM to extract free-form relations between a pair of entities. The LLM used is `gpt-4.1-mini` with maximum tokens value set to `1200`. Given a list of entities and the corresponding chunk text, we are asking the LLM to extract maximum 15 unique, high-quality free-form relations pertaining to :
```text
    - ontology relations (is_a, instance_of)
    - dependency relations (parameter_of, depends_on, derived_from)
    - operational relations (converts, maps_to)
    - equation relations (defined_as, represented_as)
    - scientific functional relations (generalizes, predicts, optimizes)
```
In addition, the LLM also outputs a brief explanation/reasoning behind assigning this relation for the entity pair and confidence score.

- Stage 2: Free-form relations becomes harder to model using a graph. Therefore, as the next stage, we classify these free-form relations into a list of allowed relations mentioned above. We use the same LLM as above to do this classification. The input variables in the prompt are source entitiy, target entity, free-form relation between them and the allowed relations. 

- To optimize latency and API costs, the second stage first passes tokens through a deterministic lemmatization step to catch plural or tense variations. We only invoke the LLM classifier for complex, ambiguous semantic mapping.

- If the secondary classification pass (Stage 2) encounters a highly unique structural relationship that doesn't fit our core mathematical Enums, the pipeline falls back to an `associated_with` edge type. This allows our downstream pipeline to still traverse the edge while alerting developers that our graph ontology needs an extension.

With this we finish extracting the semantic relationships among entity pairs.
```
Example:
    source : "logistic function"
    relation : "converts"
    target : "log-odds"
    explanation : "The logistic function converts log-odds to probabilities"
    edge_type : "semantic"
    weight : 0.95
```  

**b) Conceptual Relations:**</br> 
- Conceptual relations are the second type of relations extracted. These relations capture the information that if two entities `entity_a` and `entity_b` are co-occuring in the same context, then are they semantically related or not.
- Conceptual relations are extracted at a sentence level. So we first use `spacy`'s `en_core_web_sm` model to extract sentences from a chunk text. 
- From each sentences, we extract local entities. We use the original entity list and check which all are present in this particular sentence. We DO NOT extract new entities here.
- For each unique pair of entities, we first get their text embedding vectors. We use OpenAI's `text-embedding-3-large` model to create embeddings.
- We then compute the cosine similarity scores between the pair of embedding vectors. If the score is greater than a threshold of `0.5`, we consider that entity pair to be conceptually related and eligible to have a conceptual edge between them.
- Thus, for each unique eligible pair of entities, we assign the relation `conceptually_similar` and edge type `conceptual` with `weight` as similarity score. 
- For the explantion key, we keep the extact sentence text that is being used as is. This can provide a good tracing info to validate the relationship.

With this we finish extracting the conceptual relationships among entity pairs.
```
Example:
    source : "logit model"
    relation : "conceptually_similar"
    target : "logistic model"
    explanation : "In statistics, a logistic model (or logit model) is a statistical model that models the log-odds of an event as a linear combination of one or more independent variables."
    edge_type : "conceptual"
    weight : 0.75
``` 

**c) Contextual Relations:**</br>
- Contextual relations are the next type of relations extracted. This relation is basically saying `entity_a` and `entity_b` are co-occuring the given context. 
- Contextual relations are again extracted at a sentence level. So we first use `spacy`'s `en_core_web_sm` model to extract sentences from a chunk text. 
- From each sentences, we extract local entities. We use the original entity list and check which all are present in this particular sentence. We DO NOT extract new entities here.
- For each unique pair of entities, we assign the relation `co_occurs` and edge type `contextual` with `weight` as 0.3. We keep lower weightage for this type of edge because we want to prioritize retrieving stronger edges like "semantic" and "conceptual" during the GraphRAG stage because those edges would provide better context for question generation.
- For the explantion key, we keep the extact sentence text that is being used as is. This can provide a good tracing info to validate the relationship. 

With this we finish extracting the contextual relationships among entity pairs.
```
Example:
    source : "logit model"
    relation : "co_occurs"
    target : "logistic model"
    explanation : "In statistics, a logistic model (or logit model) is a statistical model that models the log-odds of an event as a linear combination of one or more independent variables."
    edge_type : "contextual"
    weight : 0.3
```

**d) Mentions Relations:**</br>
- This is a very simple type of relationship where we just want to capture/store what all entities are present in a chunk.
- This infomation is present in the `chunks` collections (mentioned below) too, but we also wanted this information as a part of the knowledge graph too.
- This relation will be used in the GraphRAG or in any traversal path though. It is used to cluster chunks sharing some entities.
- For all entities present in a chunk, we assign the relation `mentions` and edge type also `mentions` with `weight` as 0.2. We keep lowest weightage for this type of edge because we are not using these during graph retrieval.
```
Example:
    source : "<chunk_id>"
    relation : "co_occurs"
    target : "logistic model"
    explanation : "Entity present in the chunk"
    edge_type : "mentions"
    weight : 0.2
```

With this we have finished extracting all different types of relations required to build the entity-relation knowledge graph.

Before we close this stage, we need to perform some post-processing steps to clean and validate the relationships extracted. We do `4` post-processing steps:

1) **De-duplication:** We remove duplicated pair of relations. We want to make sure that we dont have duplicates of same relation between the same pair of entity. There should be only one relation of <relation_x> like this ```entity_a -> <relation_x> -> entity_b```. This is essentially important for `conceptual` and `contextual` relations where different sentences of the same chunk may create multiple instances of same relation between same entity pair.
2) **Validation:** We validate if the `source_entity` and `target_entity` are coming from the entity set ONLY, for all the relations extracted. Alongside, we also validate that ```source_entity != target_entity``` 
3) **Relation Standardisation:** We use the standardisation rules present in the `relation_normalization.json` file to make sure we donot have same relation in meaning between any pair of entities. In the example, we are standardising three same relations but having different form to one standard form. This reduces many repeated and redundant relations from the graph
``` 
Example: 
        "converts_from": "derived_from", 
        "converted_from": "derived_from", 
        "converted_by" : "derived_from"
```
4) **Prune Relations:** We essentially want to remove relations like ```entity_a -> <relation_x> -> entity_b and entity_b -> <relation_x> -> entity_a``` where the relationship is `conceptual` or `contextual` since these relation types are non-directed. Relation pruning is the last step of the post-processing procedure. 

With this we finish Chunk-wise Relation Extraction Stage.

**Step 8: Semantic Chunk Creation Stage:**</br>

We have created two knowledge graph each holding a very specific kind of information. The entities and relations extracted above are used to create the Entity-Relation Knowledge graph. Since the entities and relations are at chunk level, we realised we need another graph depicting the connectivity between chunks. How two chunks are related will help in creating a connected picture for the entire topic. 

The offline Semantic Chunk Graph acts as a hardwired neural network of the document's narrative flow. At retrival stage, if a vector search hits a highly specific chunk, the retrieval engine uses the pre-computed edges of the semantic chunk graph to pull in adjacent or highly similar chunks. This ensures the downstream agent receives a fluid, mathematically complete narrative without risking context fragmentation or losing critical surrounding proofs.

We thus create a Semantic Chunk Knowledge Graph and follow the below mentioned steps to do so:

We measure two things to determine if the chunks are related.
- First, we compute a cosine similarity between the embeddings of the chunk text for every pair of chunks that are created for the particular topic.
- Next, we compute shared entities list between the same pair of chunks, again across all chunks.
- If the cosine similarity is above the threshold of `0.72` or if they share a non-zero list of entities between them, then we mark these two corresponding chunks as sematically related.
- We create a graph edge between the chunk pair like this : ```source_chunk (source chunk id), target_chunk (target chunk id), shared_entities (list of common entity names), similarity (cosine similarity value)```

With this we create the second knowledge graph : Semantic Chunk Graph


**Step 9: Knowledge Hash Creation Stage:**</br>

Designed a deterministic, immutable state-tracking engine utilizing stateful canonical JSON sorting and SHA-256 payload hashing. This serves as a cryptographic version control layer for the knowledge base. 

We are creating a hash for the knowledge stored for a particular topic and the corresponding source from where the information is extracted. The question bank created at the later stage is entirely dependent on this knowledge. That means if the content of this knowledge base is changed either by adding a new source for the same topic or additional information is extracted from the same source for a particular topic, then the question bank needs to be re-generated to account for the new knowledge gathered in the collection. This requires a mechanism or a metric to track the freshness of the existing knowledge base. This same metric will also be stored in the question bank to bind the bank with the underlying knowledge base. 

Since knowledge base creation stage can occur independently of other actions, the topic specific knowledge hash can change without impacting the other stored artefacts. So, we would need to match this hash value with the one stored as a part of the question bank during question bank loading. If there is a mismatch found, we would trigger the question bank re-generation pipeline. This is how we ensure freshness of knowledge and the corresponding questions.

The metric we chose for this is Hashing. We create a source specific hash as well as topic specific hash. Topic specfic hash is created on top of each source hash. 

We follow the below steps:
- For a particular source and topic id, fetch all information stored in the MongoDB in the *chunks collection*. 
- Use the entire fetched data to create a canonical json.
- Create a sha256 HASH object on the `utf-8` encoded canonical json. Finally, get the hexadecimal string as the source specific hash for this topic.
- Store all the source specific hashes in a dictionary with source name as the key. 
- Use this overall dictionary to create a canonical json to create the topic specific hash.
- Again create a sha256 HASH object on this canonical topic json and get the hexadeciman string as the final knowledge hash covering all sources for a particular topic.

With this we have created the topic specific knowledge hash.


**Step 10: Chunk-wise MongoDB Collection Creation Stage:**</br>

We now have all information that we want to store for each chunk. With this, we move to ingest these information across different MongoDB collections.
We are storing the knowledge graph also in MongoDB for ease of retrieval and access.

- **chunk collection:** This is the first and one of the most important collection for this application. We store chunk-wise data in each document. The document structure is :</br> ``` chunk_id (unique UUID), document_id (or topic id), source_id (ex: Wikipedia), embeddings (for the chunk text), text (chunk text), entities (all entities for this chunk)```

- **entity_edges collection:** This is the Entity-Relation Knowledge Graph stored in a collection. Since entities and relationships between them are extracted at a chunk level, we are storing the knowledge graph too at chunk level. So for each chunk in the *chunk collection*, we create one document holding all the infomation. The document structure is :</br> ```chunk_id (foreign key linked with chunk collection), relation (list of all relations). Each relation is a dictionary of the structure: source, relation, target, explanation, edge_type, weight```

- **chunk_edges collection:** This is the Semantic Chunk Knowledge Graph (created in the Step 8) stored in a collection. The document structure is :</br> ```source_chunk, target_chunk, shared_entities, similarity ```. 

- **topic_knowledge_hash collection:** The topic hash (created in the Step 9) is stored in this collection. We store one document for each topic. The document structure is :</br> ```topic, sources (source specific hash), knowledge_hash (topic specific overall knowledge hash), updated_at ```. If an agent tries to initialize an interview session using an expired downstream question bank, the runtime mismatches the topic hash against `topic_knowledge_hash collection`, triggering an isolated, differential re-generation event rather than a costly global pipeline rerun

We thus have created all the collections required to hold the different aspects of the knowledge.


**Step 11: MongoDB Indices Creation Stage:**</br>

We created MongoDB indices on frequently queried fields to improve lookup and retrieval performance. 

- The *chunks collection* is indexed on `_id` and `chunk_id` for efficient chunk identification and retrieval. 
- The *chunk_edges collection* is indexed on `source_chunk` and `target_chunk` to accelerate traversal and lookup of relationships between chunks. 
- Similarly, the *entity_edges collection* is indexed on `chunk_id` to efficiently retrieve entity relationships associated with a particular chunk.

These indices reduce the need for full collection scans and improve the performance of graph traversal and knowledge retrieval operations as the number of stored chunks and relationships grows.


**Step 12: MongoDB Vector and Text Indices Creation Stage:**</br>

We created **two** MongoDB Atlas Search indices on the `chunks` collection to support efficient semantic and keyword-based retrieval.

- **vector_index:** The **vector search index** is built on the `embeddings` field using **3072-dimensional embeddings** and **cosine similarity**. The `document_id` (topic id) field is additionally configured as a filter field, enabling document-level pre-filtering before performing vector similarity search. This allows the system to retrieve semantically relevant chunks efficiently while restricting searches to specific topics when required.

- **text_index:** The **text search index** supports lexical and entity-based retrieval. The `document_id` (topic id) field is indexed as a token to enable pre-filtering, while `text` is indexed for full-text search. The `entities.normalized_text` field is also indexed to support searches based on extracted and normalized entities.

Together, these indices provide the foundation for **hybrid knowledge retrieval**, combining semantic similarity through vector search with keyword and entity-based search.


**Step 13: NetworkX Version of Knowledge Graph Creation Stage:**</br>

We store the networkX version of the `2` knowledge graphs for visualization purposes only. These graphs are stored under the `networkx_graphs` folder as `chunk_graph.gexf` and `entity_graph.gexf` files. 


We, thus, have completed the entire flow to create the knowledge base for a particular topic. When a new topic comes, we will need to spend some efforts in updating the `data.json` file with the correspoding urls for that new topic. If we are uploading a pdf for the topic, then we can skip this step. We also need to update the `topics.json` file with the topic id, topic name and tags for the new topic. Additionally, we might need to update the entity label list and the allowed relations list, incase we see a degrade in the quality of entities and relations extracted for that new topic. Rest all will work automatically.


### Capability Inventory

> Main inventory of everything the knowledge subsystem can currently do.
>
> Do not decide MCP boundaries yet. First identify the actual capabilities.

| ID | Capability | Purpose | Current Caller | MCP Candidate |
|---|---|---|---|---|
| K01 | | | | Yes / No / Maybe |
| K02 | | | | Yes / No / Maybe |
| K03 | | | | Yes / No / Maybe |
| K04 | | | | Yes / No / Maybe |
| K05 | | | | Yes / No / Maybe |

---

### Capability Details

> Create one subsection for every capability identified above.

## K01 — `<Capability Name>`

### Purpose

<!-- What does this capability actually do? -->

### Current Implementation

**Code location**

```text
<file/module/class/function>
```

**Entry point**

```python
<function/class/method>
```

### Inputs

| Input | Type | Required | Description |
|---|---|---|---|
| | | | |

### Outputs

```text
<return value / structure>
```

### Dependencies

```text
<services / repositories / GraphRAG / LLM / DB / cache / etc.>
```

### Side Effects

- [ ] None
- [ ] Database write
- [ ] Cache write
- [ ] QS bank modification
- [ ] Bucket modification
- [ ] Other:

### LLM Usage

- [ ] No LLM
- [ ] LLM

**Model:**

```text
<model>
```

**Approximate number of calls:**

```text
<number>
```

**Purpose of LLM call:**

```text
<...>
```

### Hash Dependencies

- [ ] No hash dependency
- [ ] Knowledge hash
- [ ] Prompt hash
- [ ] Other

Explain:

```text
<How hashes affect this capability>
```

### Persistence

```text
<What is read/written and where?>
```

### Failure Modes

| Failure | Current Behaviour |
|---|---|
| | |
| | |

### Performance Characteristics

```text
Expected latency:
Potentially expensive:
Blocking / async:
External dependencies:
```

### Current Call Flow

```text
<caller>
    ↓
<this capability>
    ↓
<dependency>
    ↓
<dependency>
```

### MCP Candidate

**Candidate:** Yes / No / Maybe

**Reason:**

<!-- Why should or should not this become an MCP capability? -->

**Potential MCP Tool Name:**

```text
<tool_name>
```

**Notes:**

<!-- Additional considerations -->


---


## 2. Hybrid GraphRAG / Knowledge Retrieval:

## Overview

<!-- How knowledge is represented and retrieved -->

### Architecture

```text
<fill in actual GraphRAG flow>
```

### Data Sources

```text
<...>
```

### Storage

```text
<...>
```

### Capabilities

| ID | Capability | Purpose | Current Caller | MCP Candidate |
|---|---|---|---|---|
| GR01 | | | | |
| GR02 | | | | |
| GR03 | | | | |

---

## GR01 — `<Retrieval Capability>`

### Purpose

<!-- ... -->

### Input

```text
<...>
```

### Output

```text
<...>
```

### Retrieval Strategy

```text
<graph / vector / hybrid / etc.>
```

### Dependencies

```text
<...>
```

### MCP Candidate

Yes / No / Maybe

---

# 6. Question Generation

## Overview

<!-- How question generation currently works -->

### Generation Flow

```text
<fill in actual flow>
```

### Capabilities

| ID | Capability | Purpose | Current Caller | MCP Candidate |
|---|---|---|---|---|
| QG01 | | | | |
| QG02 | | | | |
| QG03 | | | | |

---

## QG01 — `<Generate Questions>`

### Purpose

<!-- ... -->

### Inputs

| Input | Type | Required | Description |
|---|---|---|---|
| | | | |

### Output

```text
<question structure>
```

### Knowledge Dependency

```text
<How GraphRAG / retrieved knowledge affects generation>
```

### Prompt

```text
<Which prompt/configuration is used?>
```

### Prompt Hash

```text
<How prompt hash is generated>
```

### Knowledge Hash

```text
<How knowledge hash is generated/used>
```

### Validation

```text
<What happens after generation?>
```

### Persistence

```text
<What gets persisted and where?>
```

### Failure Handling

```text
<...>
```

### MCP Candidate

Yes / No / Maybe

---

# 7. Question Validation

## Overview

<!-- How generated questions are validated -->

### Validation Flow

```text
<generated question>
    ↓
<validation>
    ↓
<pass/fail>
    ↓
<persistence / regeneration / rejection>
```

### Capabilities

| ID | Capability | Purpose | Current Caller | MCP Candidate |
|---|---|---|---|---|
| VL01 | | | | |
| VL02 | | | | |

---

## VL01 — `<Validation Capability>`

### Purpose

### Input

### Output

### Validation Rules

```text
<...>
```

### Failure Behaviour

```text
<...>
```

### MCP Candidate

Yes / No / Maybe

---

# 8. QS Bank

## Purpose

<!-- What exactly is a QS bank? -->

## Data Model

```text
<question>
    ↓
<bucket / concept / difficulty / level / etc.>
    ↓
<QS Bank>
```

<!-- Replace with actual structure -->

## Bank Lifecycle

```text
<actual lifecycle>
```

### QS Bank Capabilities

| ID | Capability | Purpose | Current Caller | MCP Candidate |
|---|---|---|---|---|
| QB01 | | | | |
| QB02 | | | | |
| QB03 | | | | |

---

# 9. Get QS Bank

## QB01 — `get_qs_bank`

### Purpose

<!-- Describe the complete behaviour of get_qs_bank -->

### Current Caller

```text
Knowledge Service
```

### Current Flow

```text
Knowledge Service
    ↓
get_qs_bank
    ↓
<...>
```

### Decision Logic

```text
QS bank exists?
    │
    ├── No
    │    ↓
    │  Generate QS bank
    │
    └── Yes
         ↓
     Check freshness
         │
         ├── Current
         │      ↓
         │   Return QS bank
         │
         └── Stale
                ↓
            Regenerate QS bank
```

### Freshness Criteria

```text
<actual logic>
```

### Hashes Checked

| Hash | Purpose | Source |
|---|---|---|
| Knowledge Hash | | |
| Prompt Hash | | |
| Other | | |

### Output

```text
<QS bank structure>
```

### Side Effects

```text
<generation / regeneration / persistence / cache / etc.>
```

### Failure Handling

```text
<...>
```

### MCP Candidate

**Yes**

### Potential MCP Tool

```text
get_qs_bank
```

### Important Boundary

```text
get_qs_bank is a high-level knowledge capability.

The caller should not need to know whether the bank was:
- fetched from storage,
- generated because it did not exist, or
- regenerated because it became stale.
```

---

# 10. QS Bank Freshness

## Purpose

<!-- Explain how QS bank freshness is determined -->

### Hash Types

| Hash | Represents | Stored Where | Calculated When | Used By |
|---|---|---|---|---|
| Knowledge Hash | | | | |
| Prompt Hash | | | | |
| Other | | | | |

### Freshness Flow

```text
Stored QS Bank
    ↓
Read stored hashes
    ↓
Calculate / obtain current hashes
    ↓
Compare
    ↓
<current / stale>
```

### Regeneration Conditions

- [ ] QS bank does not exist
- [ ] Knowledge hash changed
- [ ] Prompt hash changed
- [ ] Bucket state changed
- [ ] Other:

### What Happens When Stale?

```text
<actual behaviour>
```

---

# 11. Buckets

## Bucket Model

<!-- Explain what a bucket represents -->

### Bucket Dimensions

```text
<topic>
<concept>
<difficulty>
<level>
<other dimensions>
```

### Bucket Structure

```text
<actual structure>
```

### Bucket Capabilities

| ID | Capability | Purpose | Read / Write | Current Caller | MCP Candidate |
|---|---|---|---|---|---|
| BK01 | | | | | |
| BK02 | | | | | |
| BK03 | | | | | |

---

# 12. Bucket Health

## Purpose

<!-- What makes a bucket healthy/unhealthy? -->

### Health Criteria

```text
<actual rules>
```

### Inputs

```text
<...>
```

### Outputs

```text
<...>
```

### Current Caller

```text
Maintenance Executor
```

### Trigger

```text
<every N turns / condition / etc.>
```

### MCP Candidate

Yes / No / Maybe

### Potential MCP Tool

```text
check_bucket_health
```

---

# 13. Bucket Regeneration

## Purpose

<!-- What does bucket regeneration actually do? -->

### Current Flow

```text
<fill in actual flow>
```

### Trigger

```text
<what causes regeneration?>
```

### Inputs

```text
<...>
```

### Outputs

```text
<...>
```

### Side Effects

```text
<DB / cache / QS bank / etc.>
```

### LLM Calls

```text
<number and purpose>
```

### Knowledge Dependency

```text
<...>
```

### Prompt Dependency

```text
<...>
```

### Hash Dependency

```text
<...>
```

### Persistence

```text
<...>
```

### Failure Handling

```text
<...>
```

### Current Caller

```text
Maintenance Layer
```

### MCP Candidate

Yes / No / Maybe

### Potential MCP Tool

```text
regenerate_bucket
```

---

# 14. QS Regeneration

## Purpose

<!-- What exactly gets regenerated? Entire bank / individual questions / buckets / etc. -->

### Regeneration Types

| Type | Trigger | Scope | Current Caller |
|---|---|---|---|
| | | | |
| | | | |

### Knowledge Hash Change

```text
<actual behaviour>
```

### Prompt Hash Change

```text
<actual behaviour>
```

### Regeneration Flow

```text
<fill in actual flow>
```

### Persistence

```text
<...>
```

### Failure Handling

```text
<...>
```

### MCP Candidate

Yes / No / Maybe

### Potential MCP Tool

```text
<tool name>
```

---

# 15. Persistence

## Knowledge Data

| Data | Storage | Read By | Written By |
|---|---|---|---|
| | | | |
| | | | |

## QS Bank Data

| Data | Storage | Read By | Written By |
|---|---|---|---|
| | | | |
| | | | |

## Question Data

| Data | Storage | Read By | Written By |
|---|---|---|---|
| | | | |
| | | | |

## Bucket Data

| Data | Storage | Read By | Written By |
|---|---|---|---|
| | | | |
| | | | |

---

# 16. Current Callers

> This section is important because Knowledge MCP will be shared by multiple AgeT components.

## Knowledge Service

```text
Knowledge Service
    ↓
<capability>
    ↓
<capability>
```

## Maintenance Layer

```text
Maintenance Executor
    ↓
<capability>
    ↓
<capability>
```

## Other Callers

```text
<list other callers>
```

---

# 17. Runtime vs Maintenance Usage

| Capability | Runtime | Maintenance | Both |
|---|---:|---:|---:|
| | | | |
| | | | |
| | | | |

## Runtime Flow

```text
Interview Initialization
    ↓
Knowledge Service
    ↓
get_qs_bank
    ↓
ConversationContext
    ↓
Planner
    ↓
QS Agent
    ↓
Select question from QS Bank
```

### Important Runtime Boundary

```text
The QS Agent does NOT call Knowledge MCP during
normal interview question selection.

The QS Bank is already loaded into ConversationContext
before the Planner executes.
```

---

## Maintenance Flow

```text
Background Maintenance Executor
    ↓
Every N turns
    ↓
Bucket health check
    ↓
Unhealthy?
    │
    ├── No → Done
    │
    └── Yes
          ↓
      Bucket regeneration
```

---

## Freshness Maintenance Flow

```text
Background Maintenance
    ↓
Check relevant hashes
    ↓
Knowledge hash changed?
    OR
Prompt hash changed?
    ↓
Regenerate stale QS bank / questions
```

---

# 18. Candidate MCP Tools

> Fill this section only after completing the capability inventory.

| MCP Tool | Purpose | Primary Caller | Read / Write | Agent Needed? |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

## Proposed Categories

### Runtime

```text
<tools>
```

### Retrieval

```text
<tools>
```

### Generation

```text
<tools>
```

### Bucket Management

```text
<tools>
```

### Regeneration

```text
<tools>
```

### Validation

```text
<tools>
```

---

# 19. MCP Tool Boundaries

> Define the public MCP boundary separately from the internal implementation.

## `<tool_name>`

### Purpose

<!-- What meaningful capability does this expose? -->

### Why This Should Be an MCP Capability

<!-- ... -->

### Why This Should NOT Be Split Into Smaller MCP Tools

<!-- ... -->

### Internal Operations

```text
MCP Tool
    ↓
<internal operation>
    ↓
<internal operation>
    ↓
<internal operation>
```

### Public MCP Input

```text
<schema>
```

### Public MCP Output

```text
<schema>
```

### Internal Implementation

```text
<existing services/functions>
```

### Side Effects

```text
<...>
```

### Failure Modes

```text
<...>
```

---

# 20. Agent Requirement

> Not every MCP capability requires an agent.

| Capability | Deterministic? | Agent Needed? | Reason |
|---|---:|---:|---|
| get_qs_bank | Yes | No | |
| check_bucket_health | Yes | No | |
| regenerate_bucket | | | |
| regenerate_qs_bank | | | |
| search_knowledge | | | |
| generate_questions | | | |

## Knowledge Agent Responsibilities

If a Knowledge Agent is retained:

```text
<What exactly does the agent decide?>
```

### Agent Should NOT Be Responsible For

```text
<domain logic that should remain deterministic>
```

### Agent Tool Selection

```text
Knowledge Task
    ↓
Knowledge Agent
    ↓
Available MCP Tools
    ↓
Select Tool
    ↓
Invoke Tool
```

---

# 21. MCP Access Model

## Consumers

```text
                         Knowledge MCP
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
        Knowledge Service            Maintenance Layer
                │                           │
                ▼                           ▼
          get_qs_bank                health / regeneration
```

## Consumer → Capability Mapping

| Consumer | Capability | MCP Tool |
|---|---|---|
| Knowledge Service | | |
| Maintenance Layer | | |
| Other | | |

---

# 22. Internal vs MCP Boundary

## Exposed Through MCP

```text
<high-level domain capabilities>
```

## Remains Internal

```text
<internal functions / helpers / repositories / hashing implementation / etc.>
```

### Boundary Principle

```text
MCP exposes meaningful knowledge capabilities.

Internal implementation details remain behind
the Knowledge MCP boundary.
```

---

# 23. Error Model

## Knowledge Errors

| Error | Meaning | Caller Behaviour |
|---|---|---|
| | | |
| | | |
| | | |

Potential categories:

```text
KnowledgeNotFound
InvalidKnowledgeRequest
QuestionGenerationFailed
QuestionValidationFailed
QSBankNotFound
QSBankRegenerationFailed
BucketNotFound
BucketRegenerationFailed
KnowledgeRetrievalFailed
KnowledgeTimeout
PersistenceFailure
HashCalculationFailure
```

<!-- Remove anything that doesn't actually apply -->

---

# 24. Performance / Cost Considerations

| Capability | LLM Calls | Expected Latency | Expensive? | Cacheable? |
|---|---:|---:|---:|---:|
| | | | | |
| | | | | |

## Potential Hot Paths

```text
<...>
```

## Potential Background Paths

```text
<...>
```

---

# 25. Open Questions / Things to Reconstruct

> Use this section aggressively while reviewing the existing code.

- [ ] What exactly determines bucket health?
- [ ] Where is the knowledge hash generated?
- [ ] Where is the prompt hash generated?
- [ ] Where are hashes stored?
- [ ] What happens when only the prompt hash changes?
- [ ] What happens when only the knowledge hash changes?
- [ ] Does regeneration regenerate the entire QS bank?
- [ ] Does regeneration regenerate individual questions?
- [ ] What triggers bucket regeneration?
- [ ] What triggers QS regeneration?
- [ ] Where are generated questions persisted?
- [ ] What validation happens before persistence?
- [ ] What happens if QS bank generation partially fails?
- [ ] What happens if the QS bank is empty?
- [ ] What happens if the required knowledge doesn't exist?
- [ ] Which operations are deterministic?
- [ ] Which operations invoke an LLM?
- [ ] Which operations are read-only?
- [ ] Which operations mutate state?
- [ ] What other knowledge capabilities exist?
- [ ] What capabilities are currently called directly?
- [ ] Which of those should move behind MCP?
- [ ] What should explicitly remain internal?
- [ ] Other:


# 26. Final Knowledge Capability Map

> Fill this section after the entire subsystem has been reconstructed.

```text
                         Knowledge Subsystem
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
          Retrieval            Generation         Maintenance
              │                   │                   │
              ▼                   ▼                   ▼
          <...>                <...>              <...>
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  │
                                  ▼
                              QS Bank
```

---

# 27. Final MCP Capability Set

> This is the final section to complete.
>
> It should contain only the capabilities that have been intentionally selected
> as the Knowledge MCP public interface.

## Runtime

```text
<tools>
```

## Retrieval

```text
<tools>
```

## Generation

```text
<tools>
```

## Bucket Management

```text
<tools>
```

## Regeneration

```text
<tools>
```

## Validation

```text
<tools>
```

---

## Final Tool Table

| Tool | Purpose | Caller(s) | Read / Write | LLM? | Agent Required? |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |

---

# 28. Explicitly Not Exposed Through MCP

> Internal implementation details that should remain behind the MCP boundary.

```text
<functions>
<helpers>
<repositories>
<hash implementation>
<internal orchestration>
<other implementation details>
```

---

# 29. Knowledge MCP Target Architecture

```text
                         AgeT
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
      Knowledge Service          Maintenance Layer
              │                         │
              │                         │
              ▼                         ▼
         MCP Client                MCP Client
              │                         │
              └────────────┬────────────┘
                           │
                           ▼
                    Knowledge MCP
                           │
             ┌─────────────┼──────────────┐
             │             │              │
             ▼             ▼              ▼
          Retrieval     Generation    Maintenance
             │             │              │
             └─────────────┼──────────────┘
                           ▼
                  Existing Knowledge
                     Implementation
```

## Runtime Interview Path

```text
Interview Start
    ↓
Knowledge Service
    ↓
get_qs_bank
    ↓
Knowledge MCP
    ↓
Existing / Generate / Regenerate
    ↓
QS Bank
    ↓
ConversationContext
    ↓
Planner
    ↓
QS Agent
    ↓
Select Question
```

## Maintenance Path

```text
Background Executor
    ↓
Knowledge MCP
    ↓
Bucket Health Check
    ↓
Bucket Regeneration if required
```

## Freshness Path

```text
Prompt Hash / Knowledge Hash Change
    ↓
Detected by relevant knowledge / maintenance operation
    ↓
QS Bank / Question Regeneration
    ↓
Updated persisted QS Bank
```