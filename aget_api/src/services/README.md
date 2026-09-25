<b> Redis Service </b>

Saving Interview 
```text
Pydantic ConversationContext
          │
          │ model_dump()
          ▼
    Python dictionary
          │
          │ json.dumps each field
          ▼
      Redis HSET
          │
          ▼
      Redis Hash
```

Retrieving Interview:
```text
      Redis Hash
          │
          │ HGETALL
          ▼
    Python dictionary
          │
          │ json.loads each field
          ▼
    context_data
          │
          │ model_validate()
          ▼
Pydantic ConversationContext
```

