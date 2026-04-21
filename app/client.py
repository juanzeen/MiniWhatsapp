import asyncio
import uuid
from websockets.asyncio.client import connect
import json
from utils import URI, phone_check, name_check, nickname_check, password_check, format_date

#Estilização geral do sistema
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align

#Estilização pro chat (pra não quebrar formatação entre enviar mensagem e feedback)
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML

console = Console()

pending_requests = {}

async def receiver(websocket):
    global active_chat
    while True:
        try:
            response = await websocket.recv()
            data = json.loads(response)
            req_id = data.get("request_id")

            if req_id and req_id in pending_requests:
                pending_requests[req_id].set_result(data)

            elif data["type"] == "NEW_MESSAGE":
                sender = data["sender_phone"]
                if sender == active_chat:
                    await websocket.send(json.dumps({
                        "type": "PROCESS_MESSAGE",
                        "message_id": data["message_id"],
                        "sender_phone": data["sender_phone"],
                        "receiver_phone": data["receiver_phone"],
                        "new_status": "read"
                    }))

                    print_formatted_text(HTML(f"\n<b><ansiblue>{sender}</ansiblue></b> <ansigray>[{format_date(data['timestamp'])}]:</ansigray> {data['content']}"))

                else:
                    await websocket.send(json.dumps({
                        "type": "PROCESS_MESSAGE",
                        "message_id": data["message_id"],
                        "sender_phone": data["sender_phone"],
                        "receiver_phone": data["receiver_phone"],
                        "new_status": "delivered"
                    }))

            elif data["type"] == "STATUS_UPDATE":
                # 🟢 NOVO PRINT AQUI (Adequado para as notificações do sistema)
                if data['status'] == 'read':
                    print_formatted_text(HTML("\n<ansicyan>✓✓✓</ansicyan>"))
                elif data['status'] == 'delivered':
                    print_formatted_text(HTML("\n<ansiyellow>✓✓</ansiyellow>"))

        except Exception as e:
            console.print(f"[bold red]Erro ao receber mensagem:[/bold red] {e}")
            break

async def send_messages(websocket, phone, contact_phone):
    global active_chat
    active_chat = contact_phone

    loop = asyncio.get_event_loop()

    console.rule("[bold cyan]Conversa Iniciada (/sair para voltar)[/bold cyan]")

    session = PromptSession()

    while True:
        with patch_stdout():
            text = await session.prompt_async("Você: ")

        if text.strip() == "/sair":
            active_chat = None
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

        await future
        pending_requests.pop(req_id, None)

async def login_menu(websocket, phone):
    global active_chat
    active_chat = None

    receiver_task = asyncio.create_task(receiver(websocket))
    loop = asyncio.get_event_loop()
    await asyncio.sleep(0.1)

    req_id = str(uuid.uuid4())
    future = asyncio.get_event_loop().create_future()
    pending_requests[req_id] = future
    await websocket.send(json.dumps({
        "type": "UPDATE_MESSAGES_DELIVERED",
        "request_id": req_id,
        "receiver": phone,
    }))
    try:
        data = await asyncio.wait_for(future, timeout=5)
    except asyncio.TimeoutError:
        pending_requests.pop(req_id, None)
        console.print("[dim yellow]Timeout ao atualizar mensagens para 'recebida'. Tente novamente.[/dim yellow]")
    finally:
        pending_requests.pop(req_id, None)

    while True:
        console.print(Panel("[1] Contatos\n[2] Adicionar novo contato\n[3] Logout", title="[bold blue]Área do Usuário[/bold blue]", expand=True))
        home_options = await loop.run_in_executor(None, input, ": ")

        if home_options == "1":
            req_id = str(uuid.uuid4())
            future = asyncio.get_event_loop().create_future()
            pending_requests[req_id] = future
            await websocket.send(json.dumps({
                "type": "CONTACTS_LIST",
                "request_id": req_id,
                "phone": phone
            }))
            try:
                data = await asyncio.wait_for(future, timeout=5)
            except asyncio.TimeoutError:
                pending_requests.pop(req_id, None)
                console.print("[bold red]Timeout ao obter lista de contatos. Tente novamente.[/bold red]")
            finally:
                pending_requests.pop(req_id, None)

            contacts = data["contacts"]

            if not contacts:
                console.print("[yellow]Você não possui contatos salvos. Adicione um novo contato para iniciar uma conversa.[/yellow]\n")
                continue
            else:
                table = Table(title="Seus Contatos", style="cyan")
                table.add_column("Opção", justify="center", style="bold white")
                table.add_column("Nome", style="bold blue")
                table.add_column("Telefone", style="dim")

                for i, ctt in enumerate(contacts):
                    table.add_row(str(i+1), ctt['name'], ctt['phone'])

                console.print(table)

                selected_conversation = int(await loop.run_in_executor(None, input, "Selecione o contato da conversa: ")) - 1
                contact_phone = contacts[selected_conversation]["phone"]
                contact_name = contacts[selected_conversation]["name"]

                if contact_phone:
                    status_req_id = str(uuid.uuid4())
                    status_future = asyncio.get_event_loop().create_future()
                    pending_requests[status_req_id] = status_future
                    await websocket.send(json.dumps({
                        "type": "UPDATE_MESSAGES_READ",
                        "request_id": status_req_id,
                        "sender_phone": contact_phone,
                        "receiver_phone": phone,
                    }))
                    try:
                        data = await asyncio.wait_for(status_future, timeout=5)
                    except asyncio.TimeoutError:
                        pending_requests.pop(status_req_id, None)
                        console.print("[dim yellow]Timeout ao atualizar status. Tente novamente.[/dim yellow]")
                    finally:
                        pending_requests.pop(status_req_id, None)

                msg_req_id = str(uuid.uuid4())
                msg_future = asyncio.get_event_loop().create_future()
                pending_requests[msg_req_id] = msg_future

                await websocket.send(json.dumps({
                    "type": "MESSAGE_HISTORY",
                    "request_id": msg_req_id,
                    "phone": phone,
                    "selected_contact": contact_phone
                }))
                try:
                    data = await asyncio.wait_for(msg_future, timeout=5)
                except asyncio.TimeoutError:
                    pending_requests.pop(msg_req_id, None)
                    console.print("[bold red]Timeout ao obter histórico de mensagem. Tente novamente.[/bold red]")
                finally:
                    pending_requests.pop(msg_req_id, None)

                history = data.get("messages", [])
                status_icon = {"sent": "✓", "delivered": "✓✓", "read": "✓✓✓"}

                console.rule(f"[bold cyan]Histórico de Conversa[/bold cyan]")
                for msg in history:
                    if msg["sender_phone"] == phone:
                        txt = f"Você \\[[dim]{format_date(msg['timestamp'])}[/dim]]: {msg['content']} [yellow]{status_icon[msg['status']]}[/yellow]"
                        console.print(txt, justify="right", style="bold green")
                    else:
                        txt = f"{contact_name} \\[[dim]{format_date(msg['timestamp'])}[/dim]]: {msg['content']}"
                        console.print(txt, justify="left", style="bold blue")

                await send_messages(websocket, phone, contact_phone)

        elif home_options == "2":
            new_contact = await loop.run_in_executor(None, input, "Digite o número do seu novo contato: ")
            if new_contact == phone:
                console.print("[bold red]O número do seu novo contato não pode ser igual ao seu número.[/bold red]\n")
                continue
            message = await loop.run_in_executor(None, input, f"\nNovo contato: {new_contact}\nDigite a primeira mensagem: ")

            try:
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

                try:
                    data = await asyncio.wait_for(future, timeout=5)
                except asyncio.TimeoutError:
                    pending_requests.pop(req_id, None)
                    console.print("[bold red]Timeout ao começar uma conversa. Tente novamente.[/bold red]")
                finally:
                    pending_requests.pop(req_id, None)

                if data["message_status"] == "sent":
                    console.print("[bold green]Contato adicionado com sucesso![/bold green]\n")
                else:
                    console.print("[bold red]Erro ao adicionar novo contato! Tente novamente.[/bold red]")

            except Exception as e:
                console.print(f"[bold red]Erro ao enviar mensagem ao novo contato:[/bold red] {e}")

        elif home_options == "3":
            console.print("[cyan]Efetuando Logout...[/cyan]\n")
            req_id = str(uuid.uuid4())
            future = asyncio.get_event_loop().create_future()
            pending_requests[req_id] = future
            await websocket.send(json.dumps({
                "type": "LOGOUT",
                "phone": phone,
                "request_id": req_id
            }))
            try:
                data = await asyncio.wait_for(future, timeout=5)
            except asyncio.TimeoutError:
                pending_requests.pop(req_id, None)
                console.print("[bold red]Timeout ao fazer logout. Tente novamente.[/bold red]")
            finally:
                pending_requests.pop(req_id, None)

            if data.get("logout_status") == "success":
                console.print(Align.center(Panel("[bold green]Logout efetuado com sucesso![/bold green]", expand=False)))
                receiver_task.cancel()
                try:
                    await receiver_task
                except asyncio.CancelledError:
                    pass
            else:
                console.print("[bold red]Erro ao realizar logout! Tente novamente.[/bold red]")
            break
        else:
            console.print("[bold red]Digite uma opção correta![/bold red]\n")


async def main():
    try:
        async with connect(URI) as websocket:
            while True:
                console.print(Panel("[1] Cadastro\n[2] Login\n[3] Sair do aplicativo", title="[bold magenta]Bem-vindo ao Mini Whatsapp[/bold magenta]", expand=True))
                option = input(": ")

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
                        console.print("\n[cyan]Realizando cadastro...[/cyan]")
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
                            console.print(Align.center(Panel("[bold green]Cadastro criado com sucesso! Realize o Login.[/bold green]", expand=False)))
                        elif data["register_status"] == "error":
                            console.print(Align.center(Panel(f"[bold red]Erro ao realizar o cadastro![/bold red]\nMotivo do erro: {data['reason']}\nTente novamente.", expand=False)))

                    except Exception as e:
                        console.print(f"[bold red]Erro ao enviar dados de cadastro ao servidor:[/bold red] {e}")

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
                        console.print("\n[cyan]Efetuando login...[/cyan]")
                        await websocket.send(json.dumps({
                            "type": "LOGIN",
                            "phone": phone,
                            "password": password
                        }))

                        response = await websocket.recv()
                        data = json.loads(response)

                        if data["login_status"] == "success":
                            console.print(Align.center(Panel("[bold green]Login efetuado com sucesso![/bold green]", expand=False)))
                            await login_menu(websocket, phone)

                        elif data["login_status"] == "error":
                            console.print(Align.center(Panel(f"[bold red]Erro ao realizar o login![/bold red]\nMotivo do erro: {data['reason']}\nTente novamente.", expand=False)))

                    except Exception as e:
                        console.print(f"[bold red]Erro ao enviar dados de login ao servidor:[/bold red] {e}")

                elif option == "3":
                    console.print("[cyan]Saindo do aplicativo...[/cyan]\n")
                    break

                else:
                    console.print("[bold red]Digite uma opção correta![/bold red]\n")

    except Exception as e:
        console.print(f"[bold red]Erro ao conectar ao servidor:[/bold red] {e}")

if __name__ == "__main__":
    asyncio.run(main())
