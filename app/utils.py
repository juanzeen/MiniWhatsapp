import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

server_host = os.getenv("SERVER_HOST")
server_port = os.getenv("SERVER_PORT")
URI = f"ws://{server_host}:{server_port}"

def phone_check(phone):
    if len(phone) > 20:
        print("Número de Telefone muito grande (tam max: 20)\n")
    elif len(phone) < 11:
        print("Número de Telefone muito pequeno (tam min: 11)\n")
    else:
        print("Número de Telefone inserido!\n")
        return True

def name_check(name):
    if len(name) > 100:
        print("Nome muito grande (tam max: 100)\n")
    elif len(name) < 3:
        print("Nome muito pequeno (tam min: 3)\n")
    else:
        print("Nome inserido!\n")
        return True

def nickname_check(nickname):
    if len(nickname) > 100:
        print("Nickname muito grande (tam max: 100)\n")
    elif len(nickname) == 0:
        nickname = " "
        print("Nickname inserido!\n")
        return True
    else:
        print("Nickname inserido!\n")
        return True

def password_check(password):
    if len(password) > 100:
        print("Senha muito grande (tam max: 100)\n")
    elif len(password) < 8:
        print("Senha muito pequena (tam min: 8)\n")
    else:
        print("Senha inserida!\n")
        return True

def format_date(date_str):
    date = datetime.fromisoformat(date_str)
    f_date = date.strftime("%d/%m/%Y %H:%M")
    return f_date