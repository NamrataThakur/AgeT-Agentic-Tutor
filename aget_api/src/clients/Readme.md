MCP Client Responsibilities:
```text
Connection
    │
    ├── Launch/connect to server
    ├── Open transport
    └── Initialize session

Communication
    │
    ├── Discover tools
    └── Invoke tools

Convenience interface
    │
    ├── get_question_bank()
    ├── check_bucket_health()
    ├── regenerate_bucket()
    ├── create_knowledge_base()
    ├── create_topic_packet()
    └── create_question_bank()

Lifecycle
    │
    └── Close resources
```


Connection Setup:
```text
await client.connect()
        │
        ▼
Create StdioServerParameters
        │
        ▼
Start/open stdio connection
        │
        ▼
Register stdio cleanup
        │
        ▼
Obtain read_stream and write_stream
        │
        ▼
Create ClientSession
        │
        ▼
Register session cleanup
        │
        ▼
Initialize MCP session
        │
        ▼
Connected and ready
```


While closing:
```text
        close()
          │
          ▼
  AsyncExitStack.aclose()
          │
          ▼
  Close ClientSession
          │
          ▼
  Close stdio connection
          │
          ▼
  Terminate/clean up server process
          │
          ▼
  Resources released
```