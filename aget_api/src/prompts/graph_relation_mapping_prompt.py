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