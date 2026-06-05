# Documentação MiniWhatsapp

O **MiniWhatsapp** é uma aplicação de mensagens instantâneas baseada em terminal (CLI), utilizando uma arquitetura cliente-servidor com comunicação em tempo real via WebSockets e persistência em banco de dados PostgreSQL.

## 🚀 Tecnologias Utilizadas

- **Linguagem:** Python 3.10+
- **Comunicação:** `websockets` (AsyncIO)
- **Interface CLI:** `rich`, `prompt_toolkit`
- **Banco de Dados:** PostgreSQL
- **ORM/Driver:** `psycopg2`
- **Configuração:** `python-dotenv`

---

## 🏗️ Arquitetura do Sistema

O projeto segue uma estrutura modular para separar responsabilidades:

1.  **`server.py`**: O coração da aplicação. Gerencia as conexões WebSocket, roteia as mensagens e mantém o estado dos clientes online.
2.  **`client.py`**: Interface do usuário. Lida com a entrada de dados, renderização visual e recepção assíncrona de mensagens.
3.  **`repository.py`**: Camada de acesso a dados (DAO). Contém toda a lógica SQL para interagir com o PostgreSQL.
4.  **`database.py`**: Script de inicialização que cria as tabelas necessárias.
5.  **`utils.py`**: Funções utilitárias de validação e formatação.

---

## 🗄️ Modelo de Dados

O banco de dados é composto por duas tabelas principais:

### Tabela `users`
Armazena as informações cadastrais dos usuários.
```sql
CREATE TABLE IF NOT EXISTS users (
    phone VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    nickname VARCHAR(100) NOT NULL,
    password VARCHAR(100) NOT NULL
);
```

### Tabela `messages`
Armazena o histórico de mensagens e seus respectivos status.
```sql
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_phone VARCHAR(20) NOT NULL,
    receiver_phone VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'sent', -- Status: sent, delivered, read
    FOREIGN KEY (sender_phone) REFERENCES users(phone),
    FOREIGN KEY (receiver_phone) REFERENCES users(phone)
);
```

---

## 🛠️ Funcionalidades Detalhadas

### 1. Cadastro e Autenticação
O sistema valida os dados de entrada antes de enviar para o servidor. No servidor, o `repository.py` verifica se o número já existe.

**Exemplo de Validação (`utils.py`):**
```python
def password_check(password):
    if len(password) < 8:
        print("Senha muito pequena (tam min: 8)\n")
    else:
        return True
```

### 2. Mensageria em Tempo Real
A comunicação utiliza JSON sobre WebSockets. Quando uma mensagem é enviada, o servidor tenta entregá-la imediatamente se o destinatário estiver online.

**Lógica de Roteamento no Servidor (`server.py`):**
```python
elif message_type == "CHAT":
    # Registra no banco
    res = await asyncio.to_thread(repository.register_message, ...)
    
    # Se o destinatário estiver online, envia na hora
    if receiver_phone in connected_clients:
        await connected_clients[receiver_phone].send(json.dumps({
            "type": "NEW_MESSAGE",
            "content": content,
            # ...
        }))
```

### 3. Confirmação de Leitura (Checkmarks)
O projeto implementa o sistema de status inspirado no WhatsApp real:
- `✓` (sent): Mensagem gravada no banco.
- `✓✓` (delivered): Mensagem recebida pelo cliente do destinatário.
- `✓✓✓` (read): Destinatário abriu a conversa.

**Visualização no Cliente (`client.py`):**
```python
if data['status'] == 'read':
    print_formatted_text(HTML("\n<ansicyan>✓✓✓</ansicyan>"))
```

### 4. Histórico de Conversas
Ao abrir um chat, o cliente solicita o histórico completo entre os dois números.

**Busca no Repositório (`repository.py`):**
```python
def get_messages(*, sender_phone, receiver_phone):
    # ... SQL SELECT WHERE (sender = p1 AND receiver = p2) OR (sender = p2 AND receiver = p1)
```

---

## 🚦 Como Executar

### Pré-requisitos
1. Possuir o PostgreSQL instalado.
2. Criar um arquivo `.env` na raiz com as credenciais:
   ```env
   POSTGRES_DB=miniwhatsapp
   POSTGRES_USER=seu_usuario
   POSTGRES_PASSWORD=sua_senha
   POSTGRES_PORT=5432
   SERVER_HOST=localhost
   SERVER_PORT=8765
   ```

### Passo a Passo
1.  **Instalar dependências:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Inicializar o banco de dados:**
    ```bash
    python app/database.py
    ```
3.  **Iniciar o servidor:**
    ```bash
    python app/server.py
    ```
4.  **Iniciar o cliente (em terminais diferentes):**
    ```bash
    python app/client.py
    ```

---

## 🎨 Interface Visual
A interface utiliza a biblioteca `Rich` para criar painéis e tabelas elegantes no terminal, proporcionando uma experiência de usuário superior às CLIs tradicionais.

```python
console.print(Panel("[1] Cadastro\n[2] Login", title="Bem-vindo ao Mini Whatsapp"))
```

---

## ⚠️ Desafios e Soluções (Post-Mortem)

Durante o desenvolvimento, dois problemas críticos de arquitetura foram identificados e resolvidos:

### 1. Conflitos com múltiplos `websocket.recv()`
**Problema:** Na arquitetura inicial, diferentes partes do cliente tentavam chamar `websocket.recv()` de forma concorrente (ex: o menu principal esperando um retorno de login e a tarefa de escuta de mensagens esperando um novo chat). Isso causava conflitos nas corrotinas, onde uma mensagem destinada ao chat era "capturada" por engano por outra função, quebrando a lógica do sistema.

**Solução:** Implementou-se um **Receptor Centralizado** (`receiver`). Agora, existe apenas um loop de leitura do WebSocket que distribui as mensagens baseando-se em IDs de requisição (`request_id`) ou tipos de evento.

```python
# Solução: Uso de Futures para gerenciar requisições assíncronas centralizadas
if req_id and req_id in pending_requests:
    pending_requests[req_id].set_result(data)
```

### 2. "Prompt Clobbering" (Interface Quebrada)
**Problema:** Quando o servidor enviava uma atualização de status (como o check `✓✓`) ou uma nova mensagem enquanto o usuário estava no meio da digitação, o texto era impresso na mesma linha do prompt. Isso "atropelava" a entrada do usuário, resultando em uma interface feia, confusa e difícil de usar.

**Solução:** Adoção da biblioteca `prompt_toolkit`. Utilizando o gerenciador de contexto `patch_stdout()`, o sistema agora consegue imprimir novas mensagens "empurrando" o prompt de digitação para baixo de forma limpa, sem corromper o texto que o usuário já escreveu.

```python
# Solução: Garantindo que o output não quebre o input do usuário
from prompt_toolkit.patch_stdout import patch_stdout

with patch_stdout():
    text = await session.prompt_async("Você: ")
```
