import asyncio
from typing import Callable
from .server import Server

def createServer(host: str = '0.0.0.0', port: int = 19132, **options) -> Server:
    server = Server(host, port, options)
    return server
