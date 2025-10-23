# python-bedrock

Async Python reimplementation of the Bedrock (Minecraft) network protocol.

This project provides an asyncio-based library that mirrors the structure and basic API of the original JavaScript `bedrock-protocol` prototype. It aims to offer lightweight building blocks for creating Bedrock-compatible clients and servers, packet datatypes, and transforms (serialization/encryption).

Key features
- Async client and server primitives (`createClient`, `createServer`) matching an evented API
- Connection and packet helpers in `python_bedrock.connection` and `python_bedrock.transforms`
- Packet datatypes and (de)serialization utilities under `python_bedrock.datatypes`
- Example scripts in the `examples/` folder and unit tests in `tests/`

Requirements
- Python 3.9+
- Dependencies declared in `pyproject.toml`: `aiohttp`, `pyjwt`, `cryptography`

Installation

Install from source in editable mode for development:

```bash
python -m pip install -e .
```

Or build a wheel and install (poetry/build-system is configured via `pyproject.toml`):

```bash
python -m build
python -m pip install dist/python_bedrock-*.whl
```

Quickstart

Basic client (connects to a Bedrock server and starts the reader loop):

```python
import asyncio
from python_bedrock import createClient

async def main():
	client = await createClient('127.0.0.1', 19132)

	# Register handlers
	client.on('packet', lambda pkt: print('raw packet', pkt))
	client.on('text', lambda message, source: print(f'{source}: {message}'))

	# Keep running until disconnected
	try:
		await asyncio.sleep(3600)
	finally:
		await client.disconnect()

asyncio.run(main())
```

Basic server:

```python
import asyncio
from python_bedrock import createServer

async def run_server():
	srv = createServer('0.0.0.0', 19132)

	# Register events
	srv.on('listening', lambda info: print('listening on', info))
	srv.on('connect', lambda client: print('client connected', client))

	# Start listening
	await srv.listen()

	try:
		await asyncio.Event().wait()  # run forever
	finally:
		await srv.close()

asyncio.run(run_server())
```

API overview

- `python_bedrock.createClient(host, port, **options)` — asynchronous helper that opens a TCP connection, returns a started `Client` instance. The returned `Client` implements an evented API (`on`, `off`, `_emit`) and packet helpers such as `queue(packetId, payload)` and `sendMessage(message)`.
- `python_bedrock.createServer(host, port, **options)` — returns a `Server` instance. Call `await server.listen()` to start listening. The `Server` emits events such as `listening`, `connect`, `disconnect`, and `error`. Use `server.broadcast(packetName, payload)` to send packets to all clients.
- `python_bedrock.Connection` — low-level connection wrapper used internally; exposes `send`, `receive` and `close`.
- `python_bedrock.datatypes` — packet classes with `serialize()` and `deserialize()` helpers. See `tests/test_packets.py` for examples of packet construction and roundtrip assertions.

Examples and tests

- Examples are available in the `examples/` directory (`simple_client.py`, `simple_server.py`, etc.). They are minimal stubs demonstrating API usage.
- Unit tests use `pytest`. Run the test suite with:

```bash
python -m pytest -q
```

Contributing

Contributions are welcome. For small changes, open a pull request with a clear description. Please:

- Run and update tests where appropriate
- Keep API changes backwards compatible when possible
- Follow existing code style and type hints

Notes and limitations

- This library is an independent reimplementation and does not provide complete feature parity with the original JS project. It focuses on core packet types and a small, evented runtime useful for experimentation and integration tests.
- Some example scripts are intentionally minimal and do not perform full protocol handshakes. See `python_bedrock/handshake` and `python_bedrock/auth` for more advanced pieces.

License

MIT — see the `LICENSE` file for details.

Acknowledgements

This project mirrors ideas from the JavaScript `bedrock-protocol` project. See the parent repository for protocol-level documentation and packet specifications.
