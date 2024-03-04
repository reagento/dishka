import asyncio

from arq import create_pool
from arq.connections import RedisSettings


async def main():
    pool = await create_pool(RedisSettings())
    await pool.enqueue_job("get_content")


if __name__ == "__main__":
    asyncio.run(main())
