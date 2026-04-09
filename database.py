import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5435,
    dbname='mini_whatsapp',
    user='postgres',
    password='postgres'
    )

cur = conn.cursor()

cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                phone VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                nickname VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                sender_phone VARCHAR(20) NOT NULL,
                receiver_phone VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_phone) REFERENCES users(phone),
                FOREIGN KEY (receiver_phone) REFERENCES users(phone)
            );
''')

conn.commit()
cur.close()
conn.close()
