from websockets.asyncio.server import serve
from dotenv import load_dotenv
import os
import asyncio
import json
import repository

connected_clients = {}
load_dotenv()

#Lida com as mensagens recebidas dos clientes, processa (no repository) e envia a resposta de volta para o cliente
async def handle_message(websocket, json_msg):
    message_type = json_msg.get("type")
    if message_type == "REGISTER":
        res = await asyncio.to_thread(
            repository.register_user,
            phone=json_msg.get("phone"),
            name=json_msg.get("name"),
            nickname=json_msg.get("nickname"),
            password=json_msg.get("password")
        )
        if res["register_status"] == "success":
            print("Novo usuário registrado: ", json_msg.get("phone"))
        await websocket.send(json.dumps(res))

    elif message_type == "LOGIN":
        id = json_msg.get("phone")
        res = await asyncio.to_thread(
              repository.login_user,
              phone=id,
              password=json_msg.get("password")
            )
        if res["login_status"] == "success":
            connected_clients[id] = websocket
            print(f"Usuário {id} logado com sucesso!")
        await websocket.send(json.dumps(res))

    elif message_type == "CHAT":
        sender_phone= json_msg.get("sender_phone")
        receiver_phone = json_msg.get("receiver_phone")
        content = json_msg.get("content")
        res = await asyncio.to_thread(
            repository.register_message,
            sender_phone=sender_phone,
            receiver_phone=receiver_phone,
            content=content
        )
        print(res)
        if res["register_status"] == "success":
            print(f"Mensagem de {sender_phone} para {receiver_phone} registrada com sucesso!")
        await websocket.send(json.dumps(res))

    elif message_type == "CONTACTS_LIST":
        phone= json_msg.get("phone")
        res = await asyncio.to_thread(
            repository.get_contacts,
            phone=phone
        )
        if res["contacts_status"] == "success":
            print(f"Lista de contatos de {phone} resgatada com sucesso!\n {list(res['contacts'])}")
        await websocket.send(json.dumps(res))
    elif message_type == "MESSAGE_HISTORY":
        phone1 = json_msg.get("phone")
        phone2 = json_msg.get("selected_contact")
        res = await asyncio.to_thread(
            repository.get_messages,
            sender_phone=phone1,
            receiver_phone=phone2
        )
        if res["messages_status"] == "success":
            print(f"Histórico de mensagens entre {phone1} e {phone2} resgatado com sucesso!\n {list(res['messages'])}")
        await websocket.send(json.dumps(res))

#Handler para lidar com as mensagens recebidas dos clientes, roda o tempo todo no WS
async def handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        await handle_message(websocket, data)

#Configurações de ping utilizadas para manter a conexão ativa e detectar clientes desconectados
async def main():
    try:
        async with serve(handler,
                         os.environ.get("SERVER_HOST"),
                         os.environ.get("SERVER_PORT"),
                         ping_interval=30,
                         ping_timeout=60,
                         close_timeout=10
                         ) as server:
            print("Servidor Online")
            await server.serve_forever()

    except Exception as e:
        print(f"Erro ao subir servidor: {e}")

asyncio.run(main())
