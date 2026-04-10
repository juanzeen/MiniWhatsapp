import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host='localhost',
    port=5435,
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
    )

cur = conn.cursor()

cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                phone VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                nickname VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL
            );
''')

cur.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                sender_phone VARCHAR(20) NOT NULL,
                receiver_phone VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'sent',
                FOREIGN KEY (sender_phone) REFERENCES users(phone),
                FOREIGN KEY (receiver_phone) REFERENCES users(phone)
            );
''')

conn.commit()
cur.close()
conn.close()
