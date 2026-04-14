import asyncio
from websockets.asyncio.client import connect
import json
from utils import URI, phone_check, name_check, nickname_check, password_check, format_date
from datetime import datetime

async def receive_messages(websocket):
    global active_chat

    while True:
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
            data = json.loads(response)

            if data["type"] == "NEW_MESSAGE":
                sender = data["sender_phone"]
                if sender == active_chat:
                    await websocket.send(json.dumps({
                        "type": "PROCESS_MESSAGE",
                        "message_id": data["message_id"],
                        "sender_phone": data["sender_phone"],
                        "receiver_phone": data["receiver_phone"],
                        "new_status": "read"
                    }))
                    print(f"\n{sender} [{format_date(data['timestamp'])}]: {data['content']}")
                else:
                    await websocket.send(json.dumps({
                        "type": "PROCESS_MESSAGE",
                        "message_id": data["message_id"],
                        "sender_phone": data["sender_phone"],
                        "receiver_phone": data["receiver_phone"],
                        "new_status": "delivered"
                    }))
                    print(f"\n Nova mensagem de {sender}: {data['content']}") #se bagunçar no chat, tirar isso

            print("Você: ", end="", flush=True)

        except Exception as e :
            print(f"Erro ao receber mensagem: {e}")
            break

async def send_messages(websocket, phone, contact_phone):
    global active_chat
    active_chat = contact_phone

    loop = asyncio.get_event_loop()

    print("\n--- Conversa iniciada (/sair para voltar) ---\n")
    while True:
        print("Você: ", end="", flush=True)
        text = await loop.run_in_executor(None, input, "")

        if text.strip() == "/sair":
            active_chat = None
            break

        if not text.strip():
            continue

        await websocket.send(json.dumps({
            "type": "CHAT",
            "sender_phone": phone,
            "receiver_phone": contact_phone,
            "content": text
        }))

async def login_menu(websocket, phone):
    global active_chat
    active_chat = None

    asyncio.create_task(receive_messages(websocket))

    while True:
        home_options = input("1-Contatos\n2-Adicionar novo contato\n3-Logout\n:")
        if home_options == "1":
            await websocket.send(json.dumps({
                "type": "CONTACTS_LIST",
                "phone": phone
            }))
            response = await websocket.recv()
            data = json.loads(response)
            contacts = data["contacts"]

            if not contacts:
                print("Você não possui contatos salvos. Adicione um novo contato para iniciar uma conversa.\n")
                continue

            else:
                for i, ctt in enumerate(contacts):
                    print(f"{i+1} - {ctt["name"]} ({ctt["phone"]})\n\n")

                selected_conversation = int(input("Selecione o contato da conversa: ")) - 1
                contact_phone = contacts[selected_conversation]["phone"]

                await websocket.send(json.dumps({
                    "type": "MESSAGE_HISTORY",
                    "phone": phone,
                    "selected_contact": contact_phone
                }))

                response = await websocket.recv()
                data = json.loads(response)

                history = data.get("messages", [])
                for msg in history:
                    if msg["sender_phone"] == phone:
                        print(f"Você [{format_date(msg['timestamp'])}]: {msg['content']}")
                    else:
                        print(f"{contacts[selected_conversation]["name"]} [{format_date(msg['timestamp'])}]: {msg['content']}")

                await send_messages(websocket, phone, contact_phone)

        elif home_options == "2":
            new_contact = input("Digite o número do seu novo contato: ")
            if new_contact == phone:
                print("O número do seu novo contato não pode ser igual ao seu número.\n")
                continue
            message = input(f"\nNovo contato: {new_contact}\nDigite a primeira mensagem: ")
            # só poderá adicionar um novo contato se mandar uma mensagem,
            # assim iniciando um novo histórico
            try:
                await websocket.send(json.dumps({
                    "type": "START_CHAT",
                    "sender_phone": phone,
                    "receiver_phone": new_contact,
                    "content": message
                }))

                response = await websocket.recv()
                data = json.loads(response)

                if data["message_status"] == "sent":
                    print("Contato adicionado!\n")
                else:
                    print("Erro ao adicionar novo contato! Tente novamente.")

            except Exception as e:
                print(f"Erro ao enviar mensagem ao novo contato: {e}")

        elif home_options == "3":
            print("Efetuando Logout...\n")
            break
        else:
            print("Digite uma opção correta!\n")


async def main():
    try:
        async with connect(URI) as websocket:
            while True:
                option = input("1-Cadastro\n2-Login\n3-Sair do aplicativo\n:")

                if option == "1":
                    while True:
                        phone = input("Digite seu número de telefone: ")
                        if phone_check(phone):
                            break

                    while True:
                        name = input("Digite seu nome: ")
                        if name_check(name):
                            break

                    while True:
                        nickname = input("Digite seu apelido: ")
                        if nickname_check(nickname):
                            break

                    while True:
                        password = input("Digite sua senha: ")
                        if password_check(password):
                            break

                    try:
                        print("Realizando cadastro...")
                        await websocket.send(json.dumps({
                            "type": "REGISTER",
                            "phone": phone,
                            "name": name,
                            "nickname": nickname,
                            "password": password
                        }))

                        response = await websocket.recv()
                        data = json.loads(response)

                        if data["register_status"] == "success":
                            print("Cadastro criado com sucesso! Realize o Login.\n")
                        elif data["register_status"] == "error":
                            print(f"Erro ao realizar o cadastro!\nMotivo do erro: {data["reason"]}\nTente novamente.\n")

                    except Exception as e:
                        print(f"Erro ao enviar dados de cadastro ao servidor: {e}")

                elif option == "2":
                    while True:
                        phone = input("Digite seu número de telefone: ")
                        if phone_check(phone):
                            break

                    while True:
                        password = input("Digite sua senha: ")
                        if password_check(password):
                            break

                    try:
                        print("Efetuando login...")
                        await websocket.send(json.dumps({
                            "type": "LOGIN",
                            "phone": phone,
                            "password": password
                        }))

                        response = await websocket.recv()
                        data = json.loads(response)

                        if data["login_status"] == "success":
                            print("Login efetuado com sucesso!\n")
                            await login_menu(websocket, phone)

                        elif data["login_status"] == "error":
                            print(f"Erro ao realizar o login!\nMotivo do erro: {data["reason"]}\nTente novamente.\n")

                    except Exception as e:
                        print(f"Erro ao enviar dados de login ao servidor: {e}")

                elif option == "3":
                    print("Saindo do aplicativo...\n")
                    break

                else:
                    print("Digite uma opção correta!\n")

    except Exception as e:
        print(f"Erro ao conectar ao servidor: {e}")

asyncio.run(main())
