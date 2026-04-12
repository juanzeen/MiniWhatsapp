from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def register_user(*, phone, name, nickname, password):
    conn = get_db_connection()
    if conn is None:
        return {"register_status": "error", "reason": "Database connection failed"}

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT phone FROM users WHERE phone = %s", (phone,))
            if cur.fetchone():
                return {"register_status": "error", "reason": "Phone number already registered"}

            cur.execute(
                "INSERT INTO users (phone, name, nickname, password) VALUES (%s, %s, %s, %s)",
                (phone, name, nickname, password)
            )
            conn.commit()
            return {"register_status": "success"}
    except Exception as e:
        print(f"Erro ao registrar usuário: {e}")
        return {"register_status": "error", "reason": "Database error during registration"}
    finally:
        conn.close()

def login_user(*, phone, password):
    conn = get_db_connection()
    if conn is None:
        return {"login_status": "error", "reason": "Database connection failed"}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT phone FROM users WHERE phone = %s AND password = %s", (phone, password))
            if cur.fetchone():
                return {"login_status": "success"}
            else:
                return {"login_status": "error", "reason": "Invalid phone number or password"}
    except:
        pass

def register_message(*, sender_phone, receiver_phone, content):
    conn = get_db_connection()
    if conn is None:
      return {"register_status": "error", "reason": "Database connection failed"}
    if content is None or content.strip() == "":
        return {"register_status": "error", "reason": "Message content cannot be empty"}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT phone FROM users WHERE phone = %s", (sender_phone,))
            if not cur.fetchone():
                return {"register_status": "error", "reason": "Sender phone number not registered"}
            cur.execute("SELECT phone FROM users WHERE phone = %s", (receiver_phone,))
            if not cur.fetchone():
                return {"register_status": "error", "reason": "Receiver phone number not registered"}
            cur.execute(
                "INSERT INTO messages (sender_phone, receiver_phone, content) VALUES (%s, %s, %s)",
                (sender_phone, receiver_phone, content)
            )
            conn.commit()
            return {"register_status": "success", "message_status": "sent"}
    except Exception as e:
        return {"register_status": "error", "reason": f"{e}"}

def get_messages(*, sender_phone, receiver_phone):
    conn = get_db_connection()
    if conn is None:
        return {"messages_status": "error", "reason": "Database connection failed"}
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT sender_phone, receiver_phone, content FROM messages WHERE (sender_phone = %s AND receiver_phone = %s) OR (sender_phone = %s AND receiver_phone = %s) ORDER BY id",
                (sender_phone, receiver_phone, receiver_phone, sender_phone)
            )
            messages = cur.fetchall()
            return {"messages_status": "success", "messages": [{"sender_phone": data[0], "receiver_phone": data[1], "content": data[2]} for data in messages]}
    except:
        return {"messages_status": "error", "reason": "Database error"}

def get_contacts(*, phone):
    conn = get_db_connection()
    if conn is None:
        return {"contacts_status": "error", "reason": "Database connection failed"}
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT u.name, u.phone FROM users u JOIN messages m ON (u.phone = m.sender_phone AND m.receiver_phone = %s) OR (u.phone = m.receiver_phone AND m.sender_phone = %s)",
                (phone, phone)
            )
            contacts = cur.fetchall()
            return {"contacts_status": "success", "contacts": [{"name":data[0], "phone": data[1]} for data in contacts]}
    except:
        return {"contacts_status": "error", "reason": "Database error"}
