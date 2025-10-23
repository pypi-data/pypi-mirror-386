import asyncio
import socket
from typing import Dict

async def ping(host: str, port: int = 19132, timeout: float = 3.0) -> Dict[str, object]:
    loop = asyncio.get_running_loop()
    fut = loop.run_in_executor(None, _syncPing, host, port, timeout)
    return await fut

def _syncPing(host: str, port: int, timeout: float):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return {'host': host, 'port': port, 'open': True}
    except Exception:
        return {'host': host, 'port': port, 'open': False}
    finally:
        s.close()
