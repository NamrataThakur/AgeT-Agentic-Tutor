<b>The complete interaction</b>

Browser Connects:
```text
Chainlit Browser
      │
      │ GET /events/int-123
      ▼
FastAPI SSE endpoint
      │
      ▼
SSEManager.connect("int-123")
      │
      ▼
creates queue_A
      │
      ▼
clients["int-123"] = {queue_A}
```


Background Worker:
```text
Worker
   │
   ├── ResumeState = READY
   │
   └── Redis XADD
          │
          ▼
    job.completed
```


Event Consumer:
```text
Redis Stream
      │
      ▼
EventConsumer
      │
      ▼
JobEventHandler
      │
      ▼
SSEManager.send()
```


SSE Manager:
```text
SSEManager
    │
    │ queue.put(event)
    ▼
queue_A
```


SSE Endpoint:
```text
queue_A
   │
   ▼
SSE endpoint
   │
   ▼
HTTP SSE
   │
   ▼
Browser
```


<b>Mental Model</b> 

SSE Manager is the routing layer:
```text
                    SSEManager
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   interview A    interview B    interview C
        │              │              │
      queue          queue          queue
        │              │              │
        ▼              ▼              ▼
    Browser A      Browser B      Browser C
```