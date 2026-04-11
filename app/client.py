import asyncio
from websockets.asyncio.client import connect
import json
from utils import URI, phone_check, name_check, nickname_check, password_check

async def main():
    try:
        async with connect(URI) as websocket:
            while True:
                option = input("1-Cadastro\n2-Login\n:")
                
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

                    print("Realizando cadastro...")
                    await websocket.send(json.dumps({
                        "type": "register",
                        "phone": phone,
                        "name": name,
                        "nickname": nickname,
                        "password": password
                    }))

                    response = await websocket.recv()
                    data = json.loads(response)

                    if data["register_status"] == "success":
                        ...
                    elif data["register_status"] == "error":
                        ...

                elif option == "2":
                    while True:
                        phone = input("Digite seu número de telefone: ")
                        if phone_check(phone):
                            break

                    while True:
                        password = input("Digite sua senha: ")
                        if password_check(password):
                            break

                    print("Efetuando login...")
                    await websocket.send(json.dumps({
                        "type": "login",
                        "phone": phone,
                        "password": password
                    }))

                    response = await websocket.recv()
                    data = json.loads(response)

                    if data["login_status"] == "success":
                        ...
                    elif data["login_status"] == "error":
                        ...

    except Exception as e:
        print(f"Erro ao conectar ao servidor: {e}")

asyncio.run(main())