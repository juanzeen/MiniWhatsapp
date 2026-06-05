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
active_chat = None

async def send_single_request(payload):
    try:
        async with connect(URI) as websocket:
            await websocket.send(json.dumps(payload))
            response = await websocket.recv()
            return json.loads(response)
    except Exception as e:
        console.print(f"[bold red]Erro de conexão On-Demand:[/bold red] {e}")
        return {"error": str(e)}

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
                if data['status'] == 'read':
                    print_formatted_text(HTML("\n<ansicyan>✓✓✓</ansicyan>"))
                elif data['status'] == 'delivered':
                    print_formatted_text(HTML("\n<ansiyellow>✓✓</ansiyellow>"))

        except Exception:
            break

async def chat_session(phone, contact_phone, contact_name):
    global active_chat
    active_chat = contact_phone

    try:
        async with connect(URI) as websocket:

            await websocket.send(json.dumps({"type": "IDENTIFY", "phone": phone}))
            identify_res = await websocket.recv()

            await websocket.send(json.dumps({
                "type": "UPDATE_MESSAGES_READ",
                "sender_phone": contact_phone,
                "receiver_phone": phone,
                "request_id": "sync_read"
            }))
            await websocket.recv()

            msg_req_id = str(uuid.uuid4())
            await websocket.send(json.dumps({
                "type": "MESSAGE_HISTORY",
                "request_id": msg_req_id,
                "phone": phone,
                "selected_contact": contact_phone
            }))
            hist_resp = await websocket.recv()
            history = json.loads(hist_resp).get("messages", [])

            status_icon = {"sent": "✓", "delivered": "✓✓", "read": "✓✓✓"}
            console.rule(f"[bold cyan]Chat com {contact_name}[/bold cyan]")
            for msg in history:
                if msg["sender_phone"] == phone:
                    txt = f"Você \\[[dim]{format_date(msg['timestamp'])}[/dim]]: {msg['content']} [yellow]{status_icon.get(msg['status'], '✓')}[/yellow]"
                    console.print(txt, justify="right", style="bold green")
                else:
                    txt = f"{contact_name} \\[[dim]{format_date(msg['timestamp'])}[/dim]]: {msg['content']}"
                    console.print(txt, justify="left", style="bold blue")

            receiver_task = asyncio.create_task(receiver(websocket))
            session = PromptSession()
            loop = asyncio.get_event_loop()

            while True:
                with patch_stdout():
                    text = await session.prompt_async("Você: ")

                if text.strip() == "/sair":
                    break

                if not text.strip():
                    continue

                req_id = str(uuid.uuid4())
                future = loop.create_future()
                pending_requests[req_id] = future

                await websocket.send(json.dumps({
                    "type": "CHAT",
                    "sender_phone": phone,
                    "request_id": req_id,
                    "receiver_phone": contact_phone,
                    "content": text
                }))
                try:
                    await asyncio.wait_for(future, timeout=5)
                except:
                    console.print("[red]Erro ao enviar.[/red]")
                finally:
                    pending_requests.pop(req_id, None)

            receiver_task.cancel()
            active_chat = None

    except Exception as e:
        console.print(f"[bold red]Erro na sessão de chat:[/bold red] {e}")

async def login_menu(phone):
    loop = asyncio.get_event_loop()

    await send_single_request({
        "type": "UPDATE_MESSAGES_DELIVERED",
        "receiver": phone,
    })

    while True:
        console.print(Panel("[1] Contatos\n[2] Adicionar novo contato\n[3] Logout", title="[bold blue]Área do Usuário[/bold blue]", expand=True))
        home_options = await loop.run_in_executor(None, input, ": ")

        if home_options == "1":
            data = await send_single_request({
                "type": "CONTACTS_LIST",
                "phone": phone
            })

            contacts = data.get("contacts", [])
            if not contacts:
                console.print("[yellow]Nenhum contato salvo.[/yellow]\n")
                continue

            table = Table(title="Seus Contatos", style="cyan")
            table.add_column("Opção", justify="center")
            table.add_column("Nome", style="bold blue")
            table.add_column("Telefone")

            for i, ctt in enumerate(contacts):
                table.add_row(str(i+1), ctt['name'], ctt['phone'])
            console.print(table)

            try:
                selected_input = await loop.run_in_executor(None, input, "Selecione o contato (ou 0 para voltar): ")
                if selected_input == "0": continue
                idx = int(selected_input) - 1
                contact = contacts[idx]
                await chat_session(phone, contact["phone"], contact["name"])
            except (ValueError, IndexError):
                console.print("[red]Opção inválida.[/red]")

        elif home_options == "2":
            new_contact = await loop.run_in_executor(None, input, "Número do contato: ")
            if not phone_check(new_contact): continue
            message = await loop.run_in_executor(None, input, "Primeira mensagem: ")

            res = await send_single_request({
                "type": "START_CHAT",
                "sender_phone": phone,
                "receiver_phone": new_contact,
                "content": message
            })
            if res.get("register_status") == "success":
                console.print("[green]Contato adicionado![/green]")
            else:
                console.print(f"[red]Erro: {res.get('reason')}[/red]")

        elif home_options == "3":
            await send_single_request({"type": "LOGOUT", "phone": phone})
            break

async def main():
    loop = asyncio.get_event_loop()
    while True:
        console.print(Panel("[1] Cadastro\n[2] Login\n[3] Sair", title="[bold magenta]Mini Whatsapp[/bold magenta]", expand=True))
        option = await loop.run_in_executor(None, input, ": ")

        if option == "1":
            phone = input("Telefone: ")
            name = input("Nome: ")
            nickname = input("Apelido: ")
            password = input("Senha: ")

            if all([phone_check(phone), name_check(name), password_check(password)]):
                res = await send_single_request({
                    "type": "REGISTER", "phone": phone, "name": name, "nickname": nickname, "password": password
                })
                if res.get("register_status") == "success":
                    console.print("[green]Cadastrado! Faça login.[/green]")
                else:
                    console.print(f"[red]Erro: {res.get('reason')}[/red]")

        elif option == "2":
            phone = input("Telefone: ")
            password = input("Senha: ")
            res = await send_single_request({"type": "LOGIN", "phone": phone, "password": password})

            if res.get("login_status") == "success":
                await login_menu(phone)
            else:
                console.print(f"[red]Erro: {res.get('reason')}[/red]")

        elif option == "3":
            break

if __name__ == "__main__":
    asyncio.run(main())
