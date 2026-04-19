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

    elif message_type == "LOGOUT":
        id = json_msg.get("phone")
        req_id = json_msg.get("request_id")
        if connected_clients[id]:
            connected_clients.pop(id)
            print(f"Usuário {id} deslogado com sucesso!")
            await websocket.send(json.dumps({"request_id": req_id, "logout_status": "success"}))
        else:
            await websocket.send(json.dumps({"request_id": req_id, "logout_status": "error"}))


    elif message_type == "START_CHAT":
        sender_phone= json_msg.get("sender_phone")
        receiver_phone = json_msg.get("receiver_phone")
        content = json_msg.get("content")
        req_id = json_msg.get("request_id")
        res = await asyncio.to_thread(
            repository.register_message,
            sender_phone=sender_phone,
            receiver_phone=receiver_phone,
            content=content
        )
        msg_response = res | {"request_id": req_id}
        if res["register_status"] == "success":
            print(f"Mensagem de {sender_phone} para {receiver_phone} registrada com sucesso!")
        await websocket.send(json.dumps(msg_response))

    elif message_type == "CHAT":
        sender_phone= json_msg.get("sender_phone")
        receiver_phone = json_msg.get("receiver_phone")
        content = json_msg.get("content")
        req_id = json_msg.get("request_id")
        res = await asyncio.to_thread(
            repository.register_message,
            sender_phone=sender_phone,
            receiver_phone=receiver_phone,
            content=content
        )
        msg_response = res | {"request_id": req_id}
        if res["register_status"] == "success":
            print(f"Mensagem de {sender_phone} para {receiver_phone} registrada com sucesso!")
            #Se o receiver estiver online, envia a mensagem diretamente para ele
            if receiver_phone in connected_clients:
                try:
                    await connected_clients[receiver_phone].send(json.dumps({
                     "type": "NEW_MESSAGE",
                     "receiver_phone": receiver_phone,
                     "content": content,
                     "timestamp": res.get("timestamp"),
                     "message_id": res.get("message_id"),
                    }))
                except Exception as e:
                    print(f"Erro ao enviar mensagem para {receiver_phone}: {e}")
                    connected_clients.pop(receiver_phone, None)
            try:
                await connected_clients[sender_phone].send(json.dumps({"type": "STATUS_UPDATE", "status": "sent", "message_id": res.get("message_id")}))
            except (KeyError, Exception) as e:
                print(f"Erro ao enviar STATUS_UPDATE para {sender_phone}: {e}")
            await websocket.send(json.dumps(msg_response))

    elif message_type == "CONTACTS_LIST":
        phone= json_msg.get("phone")
        req_id = json_msg.get("request_id")
        res = await asyncio.to_thread(
            repository.get_contacts,
            phone=phone
        )
        msg_response = res | {"request_id": req_id}
        if res["contacts_status"] == "success":
            print(f"Lista de contatos de {phone} resgatada com sucesso!")
        await websocket.send(json.dumps(msg_response))

    elif message_type == "MESSAGE_HISTORY":
        phone1 = json_msg.get("phone")
        phone2 = json_msg.get("selected_contact")
        req_id = json_msg.get("request_id")
        res = await asyncio.to_thread(
            repository.get_messages,
            sender_phone=phone1,
            receiver_phone=phone2
        )
        msg_response = res | {"request_id": req_id}
        if res["messages_status"] == "success":
            print(f"Histórico de mensagens entre {phone1} e {phone2} resgatado com sucesso!")
        await websocket.send(json.dumps(msg_response))

    elif message_type == "UPDATE_MESSAGES_DELIVERED":
        receiver = json_msg.get("receiver")
        req_id = json_msg.get("request_id")
        res = await asyncio.to_thread(
            repository.update_history_delivered_messages,
            receiver=receiver,
        )
        msg_response = res | {"request_id": req_id}
        if res["update_status"] == "success":
            print(f"Status de mensagens enviadas para {receiver} atualizado para 'entregue' com sucesso!")
        await websocket.send(json.dumps(msg_response))

    elif message_type == "UPDATE_MESSAGES_READ":
        sender = json_msg.get("sender_phone")
        receiver = json_msg.get("receiver_phone")
        new_status = json_msg.get("new_status")
        req_id = json_msg.get("request_id")
        res = await asyncio.to_thread(
            repository.update_history_read_messages,
            sender=sender,
            receiver=receiver
        )
        msg_response = res | {"request_id": req_id}
        if res["update_status"] == "success":
            print(f"Status de mensagens de {sender} enviadas para {receiver} atualizadps para 'lido' com sucesso!")
        await websocket.send(json.dumps(msg_response))

#Lê a mensagem e envia confirmação de leitura para o sender
    elif message_type == "PROCESS_MESSAGE":
        message_id = json_msg.get("message_id")
        sender_phone =json_msg.get("sender_phone")
        new_status = json_msg.get("new_status")
        res = await asyncio.to_thread(
            repository.update_message_status,
            message_id=message_id,
            new_status=new_status
        )
        if res["update_status"] == "success":
            print(f"Status da mensagem {message_id} atualizado para '{new_status}' com sucesso!")
        try:
            sender_ws = connected_clients.get(sender_phone)
            if sender_ws:
                await sender_ws.send(json.dumps({"type": "STATUS_UPDATE", "status": new_status, "message_id": message_id}))
        except Exception as e:
            print(f"Erro ao enviar STATUS_UPDATE para {sender_phone}: {e}")


#Handler para lidar com as mensagens recebidas dos clientes, roda o tempo todo no WS
async def handler(websocket):
    phone = None
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "LOGIN":
                phone = data.get("phone")
            await handle_message(websocket, data)
    finally:
        if phone and phone in connected_clients:
            connected_clients.pop(phone)
            print(f"Usuário {phone} desconectado.")

#Configurações de ping utilizadas para manter a conexão ativa e detectar clientes desconectados
async def main():
    try:
        async with serve(handler,
                         os.environ.get("SERVER_HOST"),
                         int(os.environ.get("SERVER_PORT")),
                         ping_interval=60,
                         ping_timeout=120,
                         close_timeout=60
                         ) as server:
            print("Servidor Online")
            await server.serve_forever()

    except Exception as e:
        print(f"Erro ao subir servidor: {e}")

asyncio.run(main())
