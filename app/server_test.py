from websockets.asyncio.server import serve
import asyncio
import json

async def handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        print(data)
        await websocket.send(json.dumps({"register_status": "success"}))

async def main():
    try:
        async with serve(handler, "127.1.1.1", 5000) as server:
            print("Servidor Online")
            await server.serve_forever()
            
    except Exception as e:
        print(f"Erro ao subir servidor: {e}")

asyncio.run(main())