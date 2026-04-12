import asyncio
from websockets.asyncio.client import connect
import json
from utils import URI, phone_check, name_check, nickname_check, password_check

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
                            while True:
                                home_options = input("1-Contatos\n2-Adicionar novo contato\n3-Logout\n:")
                                if home_options == "1":
                                    ...
                                elif home_options == "2":
                                    new_contact = input("Digite o número do seu novo contato: ")
                                    message = input(f"\nNovo contato: {new_contact}\nDigite a primeira mensagem: ")
                                    # só poderá adicionar um novo contato se mandar uma mensagem,
                                    # assim iniciando um novo histórico
                                    try:
                                        await websocket.send(json.dumps({
                                            "type": "CHAT",
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
