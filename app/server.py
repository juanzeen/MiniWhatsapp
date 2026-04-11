from websockets.asyncio.server import serve
import asyncio
import json

connected_clients = {}

async def handle_message(websocket, json_msg):
    message_type = json_msg.get("type")
    if message_type == "REGISTER":
        print("Mensagem do tipo register chegou do cliente: ", json_msg)
        await websocket.send(json.dumps({"register_status": "success"}))

    elif message_type == "LOGIN":
        print("Mensagem do tipo login chegou do cliente: ", json_msg)
        meu_id = json_msg.get("phone")
        connected_clients[meu_id] = websocket
        print(f"Usuário {meu_id} conectado! no servidor. Clientes conectados: {list(connected_clients)}")
        await websocket.send(json.dumps({"login_status": "success"}))
    elif message_type == "CHAT":
        print("Mensagem do tipo chat chegou do cliente: ", json_msg)

async def handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        await handle_message(websocket, data)

async def main():
    try:
        async with serve(handler, "127.1.1.1", 5000) as server:
            print("Servidor Online")
            await server.serve_forever()

    except Exception as e:
        print(f"Erro ao subir servidor: {e}")

asyncio.run(main())
