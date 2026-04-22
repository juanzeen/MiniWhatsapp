# Mini WhatsApp

## 📱 Visão Geral do Projeto

O MiniWhatsapp é uma aplicação de mensagens em tempo real que permite a comunicação entre usuários de forma rápida e eficiente, utilizando WebSockets para comunicação bidirecional instantânea.

## ✨ Funcionalidades

- **Mensagens em Tempo Real** - Envio e recebimento de mensagens instantâneas via WebSockets
- **Autenticação de Usuários** - Sistema seguro de registro e login
- **Gerenciamento de Contatos** - Adicione e organize seus contatos
- **Histórico de Mensagens** - Rastreamento completo de conversas anteriores
- **Status de Mensagens** - Indicadores visuais: enviado (✓), entregue (✓✓), lido (✓✓✓)
- **Detecção de Usuários Online** - Veja quem está conectado em tempo real

## 🛠️ Stack Tecnológica

- **Linguagem:** Python
- **Comunicação em Tempo Real:** WebSockets (websockets 16.0)
- **Banco de Dados:** PostgreSQL
- **Framework Async:** asyncio
- **Interface Terminal:** Rich (estilização e painéis)
- **Input de Usuário:** prompt_toolkit
- **Containerização:** Docker & Docker Compose
- **Variáveis de Ambiente:** python-dotenv

## 📋 Pré-requisitos

- Python 3.8+
- Docker e Docker Compose (opcional, para execução containerizada)
- PostgreSQL 17+ (ou via Docker)

## 🚀 Instalação e Configuração

### 1. Clone o repositório
```bash
git clone https://github.com/juanzeen/MiniWhatsapp.git
cd MiniWhatsapp
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:
```env
SERVER_HOST=localhost
SERVER_PORT=8765
POSTGRES_DB=miniwhatsapp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_aqui
POSTGRES_PORT=5432
```

### 4. Configure o banco de dados

#### Opção A: Com Docker Compose (recomendado)
```bash
docker-compose up -d
```

#### Opção B: PostgreSQL local
Certifique-se de que o PostgreSQL está instalado e execute as migrações necessárias.

## 🏗️ Arquitetura do Projeto

O MiniWhatsapp segue uma arquitetura cliente-servidor com os seguintes componentes:

- **Servidor (server.py):** Gerencia conexões WebSocket, autenticação e roteia mensagens entre clientes
- **Cliente (client.py):** Interface de linha de comando para usuários se comunicarem
- **Repository (repository.py):** Camada de acesso aos dados, interage com o PostgreSQL
- **Database (database.py):** Configuração e gerenciamento da conexão com banco de dados
- **Utils (utils.py):** Funções utilitárias e validações

### Fluxo de Comunicação
1. Cliente conecta ao servidor via WebSocket
2. Usuário realiza login/registro
3. Servidor valida credenciais no banco de dados
4. Mensagens são trocadas em tempo real entre clientes conectados
5. Status das mensagens é rastreado e atualizado
6. Histórico é persistido no PostgreSQL

## ▶️ Como Executar

### Iniciar o Servidor
```bash
cd app
python server.py
```

Você deverá ver a mensagem: `Servidor Online`

### Iniciar o Cliente
Em outro terminal:
```bash
cd app
python client.py
```

## 📁 Estrutura do Projeto

```
MiniWhatsapp/
├── app/
│   ├── server.py              # Servidor WebSocket principal
│   ├── client.py              # Cliente com interface TUI
│   ├── repository.py          # Camada de dados
│   ├── database.py            # Configuração do banco
│   └── utils.py               # Funções utilitárias
├── requirements.txt           # Dependências do projeto
├── docker-compose.yaml        # Configuração Docker
├── .env                       # Variáveis de ambiente (criar)
└── README.md                  # Este arquivo
```

## 🔐 Autenticação

O sistema utiliza validação de senha e número de telefone para autenticação segura:
- Números de telefone devem ter formato válido
- Senhas devem atender aos critérios de segurança mínimos
- As credenciais são armazenadas de forma segura no PostgreSQL

## 🐛 Troubleshooting

### Erro: "Falha ao conectar ao servidor"
- Verifique se o servidor está rodando: `python server.py`
- Confirme se `SERVER_HOST` e `SERVER_PORT` no `.env` estão corretos

### Erro: "Timeout ao conectar ao banco de dados"
- Verifique se PostgreSQL está rodando
- Com Docker: `docker-compose ps`
- Localmente: `psql -U postgres -d miniwhatsapp`

### Erro: "Módulo não encontrado"
- Reinstale as dependências: `pip install -r requirements.txt`

## 📝 Licença

Este projeto foi desenvolvido para fins educacionais.

## 👨‍💻 Autor

Juan - [GitHub](https://github.com/juanzeen)
Vinícius - [GitHub](https://github.com/viniciushissa)
