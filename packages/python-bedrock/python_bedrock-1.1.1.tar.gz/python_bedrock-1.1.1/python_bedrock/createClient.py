import asyncio
from .client import Client

async def createClient(host: str = 'localhost', port: int = 19132, **options) -> Client:
    reader, writer = await asyncio.open_connection(host, port)
    client = Client(reader, writer, options)
    await client.start()
    return client
