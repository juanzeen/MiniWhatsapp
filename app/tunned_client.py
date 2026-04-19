import asyncio
import uuid
from websockets.asyncio.client import connect
import json
from utils import URI, phone_check, name_check, nickname_check, password_check, format_date
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.rule import Rule

pending_requests = {}
active_chat = None
console = Console()

STATUS_ICON = {
    "sent": "[dim]✓[/dim]",
    "delivered": "[cyan]✓✓[/cyan]",
    "read": "[green]✓✓[/green]🟢"
}


def ui_info(message):
    console.print(f"[bold cyan]{message}[/bold cyan]")


def ui_success(message):
    console.print(f"[bold green]{message}[/bold green]")


def ui_error(message):
    console.print(f"[bold red]{message}[/bold red]")


async def ainput(prompt_text, *, password=False):
    loop = asyncio.get_event_loop()

    def _ask():
        return Prompt.ask(prompt_text, password=password)

    return await loop.run_in_executor(None, _ask)


def render_main_menu():
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_row("[bold]1[/bold] Cadastro")
    table.add_row("[bold]2[/bold] Login")
    table.add_row("[bold]3[/bold] Sair")
    console.print(Panel(table, title="MiniWhatsapp", border_style="cyan"))


def render_home_menu(phone):
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_row("[bold]1[/bold] Contatos")
    table.add_row("[bold]2[/bold] Adicionar novo contato")
    table.add_row("[bold]3[/bold] Logout")
    console.print(Panel(table, title=f"Menu ({phone})", border_style="blue"))


def render_contacts(contacts):
    table = Table(title="Contatos", border_style="magenta")
    table.add_column("#", justify="right", style="bold")
    table.add_column("Nome", style="cyan")
    table.add_column("Telefone", style="green")
    for i, contact in enumerate(contacts, start=1):
        table.add_row(str(i), contact["name"], contact["phone"])
    console.print(table)


def render_history(history, my_phone, contact_name):
    console.print(Rule("Histórico", style="cyan"))
    for msg in history:
        timestamp = format_date(msg["timestamp"])
        if msg["sender_phone"] == my_phone:
            status = STATUS_ICON.get(msg.get("status", "sent"), "?")
            text = f"Você [{timestamp}]: {msg['content']}"
            console.print(f"{text[:120]:<120}  {status}")
        else:
            text = f"{contact_name} [{timestamp}]: {msg['content']}"
            console.print(f"{text[:120]:<120}")
    console.print(Rule(style="cyan"))


async def await_response(req_id, future, *, timeout=5, timeout_message="Timeout aguardando resposta do servidor."):
    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        ui_error(timeout_message)
        return None
    finally:
        pending_requests.pop(req_id, None)

async def receiver(websocket):
    global active_chat
    while True:
        try:
            response = await websocket.recv()
            data = json.loads(response)
            req_id = data.get("request_id")

            if req_id and req_id in pending_requests:
                future = pending_requests[req_id]
                if not future.done():
                    future.set_result(data)

            elif data.get("type") == "NEW_MESSAGE":
                sender = data["sender_phone"]
                if sender == active_chat:
                    await websocket.send(json.dumps({
                        "type": "PROCESS_MESSAGE",
                        "message_id": data["message_id"],
                        "sender_phone": data["sender_phone"],
                        "receiver_phone": data["receiver_phone"],
                        "new_status": "read"
                    }))
                    console.print(f"\n[bold cyan]{sender}[/bold cyan] [{format_date(data['timestamp'])}]: {data['content']}")
                else:
                    await websocket.send(json.dumps({
                        "type": "PROCESS_MESSAGE",
                        "message_id": data["message_id"],
                        "sender_phone": data["sender_phone"],
                        "receiver_phone": data["receiver_phone"],
                        "new_status": "delivered"
                    }))
                    console.print(Panel(f"Nova mensagem de [bold]{sender}[/bold]", border_style="yellow"))

            elif data.get("type") == "STATUS_UPDATE":
                icon = STATUS_ICON.get(data.get("status"), "?")
                console.print(f"\nStatus da mensagem {data.get('message_id')}: {icon}")


        except Exception as e :
            ui_error(f"Erro ao receber mensagem: {e}")
            break

async def send_messages(websocket, phone, contact_phone):
    global active_chat
    active_chat = contact_phone

    loop = asyncio.get_event_loop()
    console.print(Panel("Digite mensagens e use /sair para voltar", title=f"Conversa com {contact_phone}", border_style="green"))
    console.print(Rule("Área de entrada", style="green"))
    while True:
        text = await loop.run_in_executor(None, lambda: Prompt.ask("[bold green]Você[/bold green]"))

        if text.strip() == "/sair":
            active_chat = None
            console.print(Rule(style="green"))
            break

        if not text.strip():
            continue

        future = loop.create_future()
        req_id = str(uuid.uuid4())
        pending_requests[req_id] = future

        await websocket.send(json.dumps({
            "type": "CHAT",
            "sender_phone": phone,
            "request_id": req_id,
            "receiver_phone": contact_phone,
            "content": text
        }))

        response = await await_response(
            req_id,
            future,
            timeout=5,
            timeout_message="Timeout ao enviar mensagem."
        )
        if response and response.get("register_status") != "success":
            ui_error(f"Falha no envio: {response.get('reason', 'erro desconhecido')}")

async def login_menu(websocket, phone):
    global active_chat
    active_chat = None

    receiver_task = asyncio.create_task(receiver(websocket))
    loop = asyncio.get_event_loop()
    await asyncio.sleep(0.1)

    try:
        while True:
            render_home_menu(phone)
            home_options = await ainput("Escolha")

            if home_options == "1":
                req_id = str(uuid.uuid4())
                future = asyncio.get_event_loop().create_future()
                pending_requests[req_id] = future
                await websocket.send(json.dumps({
                    "type": "CONTACTS_LIST",
                    "request_id": req_id,
                    "phone": phone
                }))

                data = await await_response(
                    req_id,
                    future,
                    timeout=5,
                    timeout_message="Timeout ao obter lista de contatos."
                )
                if not data:
                    continue

                contacts = data.get("contacts", [])
                if not contacts:
                    ui_info("Você não possui contatos salvos.")
                    continue

                render_contacts(contacts)

                selected_raw = await ainput("Selecione o contato da conversa")
                if not selected_raw.isdigit():
                    ui_error("Seleção inválida.")
                    continue

                selected_conversation = int(selected_raw) - 1
                if selected_conversation < 0 or selected_conversation >= len(contacts):
                    ui_error("Contato fora da lista.")
                    continue

                contact_phone = contacts[selected_conversation]["phone"]
                contact_name = contacts[selected_conversation]["name"]

                msg_req_id = str(uuid.uuid4())
                msg_future = asyncio.get_event_loop().create_future()
                pending_requests[msg_req_id] = msg_future

                await websocket.send(json.dumps({
                    "type": "MESSAGE_HISTORY",
                    "request_id": msg_req_id,
                    "phone": phone,
                    "selected_contact": contact_phone
                }))

                history_response = await await_response(
                    msg_req_id,
                    msg_future,
                    timeout=5,
                    timeout_message="Timeout ao obter histórico de mensagens."
                )
                if not history_response:
                    continue

                history = history_response.get("messages", [])
                render_history(history, phone, contact_name)
                await send_messages(websocket, phone, contact_phone)

            elif home_options == "2":
                new_contact = await ainput("Digite o número do novo contato")
                if new_contact == phone:
                    ui_error("O número do novo contato não pode ser igual ao seu.")
                    continue

                message = await ainput(f"Primeira mensagem para {new_contact}")
                req_id = str(uuid.uuid4())
                future = asyncio.get_event_loop().create_future()
                pending_requests[req_id] = future

                await websocket.send(json.dumps({
                    "type": "START_CHAT",
                    "request_id": req_id,
                    "sender_phone": phone,
                    "receiver_phone": new_contact,
                    "content": message
                }))

                data = await await_response(
                    req_id,
                    future,
                    timeout=5,
                    timeout_message="Timeout ao começar conversa."
                )
                if not data:
                    continue

                if data.get("message_status") == "sent":
                    ui_success("Contato adicionado.")
                else:
                    ui_error("Erro ao adicionar novo contato.")

            elif home_options == "3":
                ui_info("Efetuando logout...")
                req_id = str(uuid.uuid4())
                future = asyncio.get_event_loop().create_future()
                pending_requests[req_id] = future
                await websocket.send(json.dumps({
                    "type": "LOGOUT",
                    "phone": phone,
                    "request_id": req_id
                }))

                data = await await_response(
                    req_id,
                    future,
                    timeout=5,
                    timeout_message="Timeout ao fazer logout."
                )
                if data and data.get("logout_status") == "success":
                    ui_success("Logout efetuado com sucesso.")
                else:
                    ui_error("Erro ao realizar logout.")
                break
            else:
                ui_error("Digite uma opção correta.")
    finally:
        receiver_task.cancel()
        try:
            await receiver_task
        except asyncio.CancelledError:
            pass


async def main():
    try:
        async with connect(URI) as websocket:
            while True:
                render_main_menu()
                option = await ainput("Escolha")

                if option == "1":
                    while True:
                        phone = await ainput("Digite seu número de telefone")
                        if phone_check(phone):
                            break

                    while True:
                        name = await ainput("Digite seu nome")
                        if name_check(name):
                            break

                    while True:
                        nickname = await ainput("Digite seu apelido")
                        if nickname_check(nickname):
                            break

                    while True:
                        password = await ainput("Digite sua senha", password=True)
                        if password_check(password):
                            break

                    try:
                        ui_info("Realizando cadastro...")
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
                            ui_success("Cadastro criado com sucesso! Realize o login.")
                        elif data["register_status"] == "error":
                            ui_error(f"Erro no cadastro: {data['reason']}")

                    except Exception as e:
                        ui_error(f"Erro ao enviar cadastro: {e}")

                elif option == "2":
                    while True:
                        phone = await ainput("Digite seu número de telefone")
                        if phone_check(phone):
                            break

                    while True:
                        password = await ainput("Digite sua senha", password=True)
                        if password_check(password):
                            break

                    try:
                        ui_info("Efetuando login...")
                        await websocket.send(json.dumps({
                            "type": "LOGIN",
                            "phone": phone,
                            "password": password
                        }))

                        response = await websocket.recv()
                        data = json.loads(response)

                        if data["login_status"] == "success":
                            ui_success("Login efetuado com sucesso.")
                            await login_menu(websocket, phone)

                        elif data["login_status"] == "error":
                            ui_error(f"Erro no login: {data['reason']}")

                    except Exception as e:
                        ui_error(f"Erro ao enviar login: {e}")

                elif option == "3":
                    ui_info("Saindo do aplicativo...")
                    break

                else:
                    ui_error("Digite uma opção correta.")

    except Exception as e:
        ui_error(f"Erro ao conectar ao servidor: {e}")

asyncio.run(main())
