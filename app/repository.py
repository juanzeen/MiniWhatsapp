from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import OperationalError, IntegrityError
from exceptions import MiniWhatsappError, AuthenticationError, DatabaseConnectionError, ValidationError, ResourceNotFoundError

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            connect_timeout=5
        )
        return conn
    except OperationalError as e:
        print(f"Erro crítico de conexão ao banco de dados: {e}")
        raise DatabaseConnectionError("Falha na conexão com o banco de dados")

def register_user(*, phone, name, nickname, password):
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT phone FROM users WHERE phone = %s", (phone,))
                if cur.fetchone():
                    raise ValidationError("Número de telefone já cadastrado")

                cur.execute(
                    "INSERT INTO users (phone, name, nickname, password) VALUES (%s, %s, %s, %s)",
                    (phone, name, nickname, password)
                )
        return {"register_status": "success"}
    except (DatabaseConnectionError, ValidationError) as e:
        raise e
    except IntegrityError:
        raise ValidationError("Erro de integridade de dados")
    except Exception as e:
        print(f"Erro inesperado ao registrar usuário: {e}")
        raise MiniWhatsappError("Erro interno do servidor")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def login_user(*, phone, password):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT phone FROM users WHERE phone = %s AND password = %s", (phone, password))
            if cur.fetchone():
                return {"login_status": "success"}
            else:
                raise AuthenticationError("Número de telefone ou senha inválidos")
    except (DatabaseConnectionError, AuthenticationError) as e:
        raise e
    except Exception as e:
        print(f"Erro inesperado no login: {e}")
        raise MiniWhatsappError("Erro interno no servidor")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def register_message(*, sender_phone, receiver_phone, content):
    if not content or not content.strip():
        raise ValidationError("O conteúdo da mensagem não pode ser vazio")

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT phone FROM users WHERE phone = %s", (sender_phone,))
                if not cur.fetchone():
                    raise ResourceNotFoundError("Remetente não encontrado")

                cur.execute("SELECT phone FROM users WHERE phone = %s", (receiver_phone,))
                if not cur.fetchone():
                    raise ResourceNotFoundError("Destinatário não encontrado")

                cur.execute(
                    """INSERT INTO messages (sender_phone, receiver_phone, content)
                    VALUES (%s, %s, %s)
                    RETURNING id, timestamp, status
                    """,
                    (sender_phone, receiver_phone, content)
                )
                row = cur.fetchone()
                return {
                    "register_status": "success",
                    "message_id": row[0],
                    "timestamp": row[1].isoformat(),
                    "message_status": row[2]
                }
    except (DatabaseConnectionError, ValidationError, ResourceNotFoundError) as e:
        raise e
    except Exception as e:
        print(f"Erro ao registrar mensagem: {e}")
        raise MiniWhatsappError("Falha ao salvar mensagem no banco")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def get_messages(*, sender_phone, receiver_phone):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """SELECT sender_phone, receiver_phone, content, timestamp, status
                FROM messages
                WHERE (sender_phone = %s AND receiver_phone = %s)
                   OR (sender_phone = %s AND receiver_phone = %s)
                ORDER BY id""",
                (sender_phone, receiver_phone, receiver_phone, sender_phone)
            )
            messages = cur.fetchall()
            return {
                "messages_status": "success",
                "messages": [
                    {
                        "sender_phone": data[0],
                        "receiver_phone": data[1],
                        "content": data[2],
                        "timestamp": data[3].isoformat(),
                        "status": data[4]
                    } for data in messages
                ]
            }
    except DatabaseConnectionError as e:
        raise e
    except Exception as e:
        print(f"Erro ao recuperar histórico: {e}")
        raise MiniWhatsappError("Erro ao buscar histórico")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def update_message_status(*, message_id, new_status):
    if new_status not in ("sent", "delivered", "read"):
        raise ValidationError("Status inválido")

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE messages SET status = %s WHERE id = %s", (new_status, message_id))
                if cur.rowcount == 0:
                    raise ResourceNotFoundError("Mensagem não encontrada")
                return {"update_status": "success", "status": new_status}
    except (DatabaseConnectionError, ValidationError, ResourceNotFoundError) as e:
        raise e
    except Exception as e:
        print(f"Erro ao atualizar status: {e}")
        raise MiniWhatsappError("Erro ao atualizar status no banco")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def update_history_delivered_messages(*, receiver):
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE messages SET status = %s WHERE receiver_phone = %s AND status = %s", ("delivered", receiver, "sent"))
                updated_count = cur.rowcount
                return {"update_status": "success", "updated_count": updated_count}
    except DatabaseConnectionError as e:
        raise e
    except Exception as e:
        print(f"Erro ao atualizar mensagens entregues: {e}")
        raise MiniWhatsappError("Erro no banco de dados")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def update_history_read_messages(*, sender, receiver):
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE messages SET status = %s WHERE sender_phone = %s AND receiver_phone = %s AND status != 'read'", ("read", sender, receiver))
                updated_count = cur.rowcount
                return {"update_status": "success", "updated_count": updated_count}
    except DatabaseConnectionError as e:
        raise e
    except Exception as e:
        print(f"Erro ao atualizar mensagens lidas: {e}")
        raise MiniWhatsappError("Erro no banco de dados")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def get_contacts(*, phone):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """SELECT DISTINCT u.name, u.phone
                FROM users u
                JOIN messages m ON (u.phone = m.sender_phone AND m.receiver_phone = %s)
                                OR (u.phone = m.receiver_phone AND m.sender_phone = %s)""",
                (phone, phone)
            )
            contacts = cur.fetchall()
            return {"contacts_status": "success", "contacts": [{"name": data[0], "phone": data[1]} for data in contacts]}
    except DatabaseConnectionError as e:
        raise e
    except Exception as e:
        print(f"Erro ao buscar contatos: {e}")
        raise MiniWhatsappError("Erro interno ao buscar contatos")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
