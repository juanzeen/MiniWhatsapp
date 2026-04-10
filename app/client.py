import socket
import threading
import json
from checks import phone_check, name_check, nickname_check, password_check

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(('127.1.1.1', 5000))
except Exception as e:
    print(f"Erro ao conectar ao servidor: {e}")

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
        client.send(json.dumps({
            "type": "register",
            "phone": phone,
            "name": name,
            "nickname": nickname,
            "password": password
        }).encode())
        
        response = client.recv(1024)
        data = json.loads(response.decode())

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
        client.send(json.dumps({
            "type": "login",
            "phone": phone,
            "password": password
        }).encode())
        
        response = client.recv(1024)
        data = json.loads(response.decode())

        if data["login_status"] == "success":
            ...

        elif data["login_status"] == "error":
            ...