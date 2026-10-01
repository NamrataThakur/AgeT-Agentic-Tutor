"""
Connection to Redis Cloud.
"""
import os
import asyncio
from dotenv import load_dotenv
from redis.asyncio import Redis

load_dotenv()

redis_url = os.getenv("REDIS_URL")

# --- Async Connection Format --------:

redis_client = Redis.from_url(url=redis_url, decode_responses=True)


# ---- Test Async Version ------- :
async def main():

    success = await redis_client.set("foo","bar")

    print("SET:", success)

    result = await redis_client.get("foo")

    print("GET:", result)

    await redis_client.aclose()


# ----Alternative Connection Format -----:

# redis_client = redis.Redis(
#     host='ink-violet-rice-39614.db.redis.io',
#     port=15613,
#     decode_responses=True,
#     username="default",
#     password="GXLAL1oStI5pBMKWjuuZ8h6tpEeyE09V",
# )



# --- TESTING THE CONNECTION -----:
#--- Async Version ----:
if __name__ == "__main__":
    asyncio.run(main())


# --- Sync Version -----:
# if __name__ == "__main__":
#     success = redis_client.set('foo', 'bar')
#     result = redis_client.get('foo')
#     print(result)



