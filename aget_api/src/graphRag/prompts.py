RELATION_EXTRACTION_PROMPT = """
        You are an expert scientific knowledge graph extractor.

        Your job:
        Extract ONLY meaningful scientific relations between the provided entities present in the chunk given.

        IMPORTANT RULES:
        - Use ONLY entities from the provided entity list.
        - Do NOT invent entities.
        - Do NOT invent relation.
        - Prefer high-quality semantic relations.
        - Ignore weak associations.
        - Extract:
            - ontology relations
            - dependency relations
            - operational relations
            - equation relations
            - scientific functional relations

        CRITICAL RULES:

            - NEVER use entities outside the entity list. Do NOT invent entities.
            - Maximum 15 relations.
            - NEVER repeat the same relation.
            - NEVER generate duplicate edges.
            - Prefer high-quality relations only.
            - Ignore weak or repetitive relations.
            - If multiple identical relations exist, output only ONE.
            - ONLY extract relations explicitly stated or strongly implied in the chunk.
            - If no relation matches exactly, choose the closest one. NEVER invent new relation names.
            - Do NOT use outside knowledge to generate relation or entity.
            - Do NOT paraphrase relations into different scientific meanings. Use the closest exact semantic relation.

        IMPORTANT : 
        Extract relations ONLY from the text present in the chunk given.
        Do NOT give general relations. Make sure relations come from the chunk ONLY.
        Relation can be free-form English but MAKE SURE it comes ONLY from the chunk text.
        Make sure the source and target entities are ONLY from the entity list provided. Do NOT invent entities.
        NEVER invent relations.

        ENTITY LIST:
        {entity_list}

        TEXT:
        \"\"\"
        {chunk}
        \"\"\"

        Examples:

        GOOD:
        - logistic regression estimates parameter
        - logistic function converts log-odds
        - probability depends_on beta_0

        BAD:
        - random co-occurrence
        - vague relations
        - hallucinated concepts

        OUtput Example:
                {{
                "source": "logistic function",
                "relation": "converts",
                "target": "log-odds",
                "confidence": 0.97,
                "edge_type": "semantic",
                "explanation" : "Logistic function is used to convert log-odds to probabilities"
                }}   

        Return only valid structured output.

"""


GRAPH_RELATION_MAPPING_PROMPT = """
            Map the relation to EXACTLY ONE ontology relation from the Allowed Relations.

            Source:
            {source}

            Raw Relation:
            {raw_relation}

            Target:
            {target}

            Allowed Relations:
            {ALLOWED_RELATIONS}

            Rules:
            - Choose ONLY one.
            - NEVER invent new relations.
            - If uncertain use "associated_with".
            - MAKE SURE to map to One of the Allowed Relations.
            - Do NOT use any other relations for mappings.
"""