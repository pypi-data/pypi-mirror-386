import asyncio
from typing import Any, Callable, Dict, Set, Optional, Union
from .connection import Connection
from .client import Client
from .types import EventCallback

class Server:
    """Async Bedrock protocol server."""
    def __init__(self, host: str, port: int, options: Dict[str, Any] = None):
        self.host = host
        self.port = port
        self.options = options or {}
        self._listeners: Dict[str, list[EventCallback]] = {}
        self._server: Optional[asyncio.Server] = None
        self._clients: Set[Client] = set()
        self._closeLock = asyncio.Lock()
        self._maxClients = self.options.get('maxClients', 10)
        self._running = False

    async def __aenter__(self) -> 'Server':
        await self.listen()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def listen(self):
        """Start listening for connections."""
        if self._server is not None:
            return
        
        self._running = True
        self._server = await asyncio.start_server(
            self._handleClient,
            self.host,
            self.port,
            limit=32768  # 32KB buffer limit
        )
        
        # Start serving
        serve_task = asyncio.create_task(self._server.serve_forever())
        serve_task.add_done_callback(self._onServeDone)
        
        await self._emit('listening', {'host': self.host, 'port': self.port})

    def _onServeDone(self, task: asyncio.Task):
        """Handle server task completion."""
        try:
            task.result()
        except Exception as e:
            asyncio.create_task(self._emit('error', e))

    async def _handleClient(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new client connection."""
        if len(self._clients) >= self._maxClients:
            writer.close()
            await writer.wait_closed()
            return

        # Create and track client
        client = Client(reader, writer, self.options)
        self._clients.add(client)
        
        try:
            await client.start()
            await self._emit('connect', client)
            
            # Set up client disconnect cleanup
            def cleanup(client=client):
                self._clients.discard(client)
                asyncio.create_task(self._emit('disconnect', client))
            
            client.on('disconnect', cleanup)
            
            # Wait for client to disconnect
            while not client.conn.isClosed:
                await asyncio.sleep(1)
                
        except Exception as e:
            await self._emit('error', e)
        finally:
            self._clients.discard(client)
            await client.disconnect()

    def on(self, event: str, callback: EventCallback) -> 'Server':
        """Register an event handler."""
        self._listeners.setdefault(event, []).append(callback)
        return self

    def off(self, event: str, callback: Optional[EventCallback] = None) -> 'Server':
        """Remove an event handler."""
        if callback is None:
            self._listeners.pop(event, None)
        else:
            handlers = self._listeners.get(event, [])
            self._listeners[event] = [cb for cb in handlers if cb != callback]
        return self

    async def _emit(self, event: str, *args, **kwargs):
        """Emit an event to all registered handlers."""
        for cb in self._listeners.get(event, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(*args, **kwargs)
                else:
                    cb(*args, **kwargs)
            except Exception as e:
                await self._emit('error', e)

    async def broadcast(self, packetName: str, payload: Dict[str, Any]):
        """Broadcast a packet to all connected clients."""
        for client in self._clients:
            try:
                await client.queue(packetName, payload)
            except Exception as e:
                await self._emit('error', e)

    async def close(self):
        """Stop the server and disconnect all clients."""
        async with self._closeLock:
            if not self._running:
                return
                
            self._running = False
            
            # Stop accepting new connections
            if self._server:
                self._server.close()
                await self._server.wait_closed()
                self._server = None
            
            # Disconnect all clients
            clients = list(self._clients)
            await asyncio.gather(
                *(client.disconnect("Server shutting down") for client in clients),
                return_exceptions=True
            )
            
            self._clients.clear()
            await self._emit('close')
