
# Nexa API – Backend com REST e Websockets

Bem-vindo ao backend do projeto Nexa! Este servidor é o núcleo inteligente do sistema de classificação de partnumbers, projetado para alta performance, escalabilidade e integração transparente com sistemas de IA.

---

## Índice
1. [Visão Geral](#visão-geral)
2. [Documentação](#documentação)
3. [O que este servidor faz](#o-que-este-servidor-faz)
4. [Arquitetura e Justificativa Técnica](#arquitetura-e-justificativa-técnica)
5. [Tecnologias Utilizadas](#tecnologias-utilizadas)
6. [Como rodar localmente](#como-rodar-localmente)
7. [Como fazer deploy](#como-fazer-deploy)
8. [Estrutura do Projeto](#estrutura-do-projeto)

---

## Documentação

- [Documentação da API (comunicação frontend ↔️ Nexa-api)](docs/api.md)
- [Integração Nexa-api ↔️ Servidor de IA](docs/ai_server_integration.md)

---

## O que este servidor faz

O Nexa API é responsável por:
- Receber requisições de classificação de partnumbers via HTTP REST.
- Orquestrar o processamento assíncrono dessas tarefas, integrando-se a um servidor de IA externo.
- Gerenciar e notificar o progresso e o resultado final para o frontend em tempo real via WebSocket (Socket.IO).
- Garantir rastreabilidade, robustez e escalabilidade em todo o fluxo de classificação.

**Em resumo:**
> O Nexa API transforma pedidos de classificação em experiências rápidas, confiáveis e integradas, conectando o usuário final à inteligência artificial de forma transparente.

---

## Real-Time Event-Driven Architecture

O **Nexa API** adota uma arquitetura **híbrida e orientada a eventos**, combinando comunicação síncrona (HTTP/REST) e assíncrona (WebSocket e Pub/Sub) para oferecer baixa latência e alta escalabilidade:

* **Flask + Flask-RESTful + Flask-SocketIO**: Servem **API REST** e **API WebSocket** no mesmo backend, permitindo operações CRUD tradicionais e comunicação em tempo real (notificações, streaming de dados) sem duplicação de infraestrutura.
* **Celery + Redis**: Gerenciam **tarefas assíncronas** de alto custo computacional, garantindo que o processamento pesado não bloqueie as respostas ao usuário.
* **Redis Pub/Sub**: Atua como **barramento de mensagens** entre o backend e o microsserviço de IA, propagando eventos de progresso e resultados em tempo real de maneira eficiente e tolerante a falhas.
* **Pydantic**: Fornece **validação e tipagem robusta** para os dados de entrada/saída, aumentando a segurança e a confiabilidade em toda a aplicação.

**Por que essa arquitetura?**
* **Feedback em Tempo Real**: Para evitar travamentos ou timeouts em chamadas HTTP convencionais, a comunicação de resultados e progresso é feita via WebSocket.Ela garante que o cliente receba atualizações contínuas (streaming) sem precisar reabrir conexões.
* **Baixa latência e comunicação em tempo real**: ideal para aplicações que exigem feedback instantâneo.
* **Desacoplamento e tolerância a falhas**: Pub/Sub garante que mensagens não dependam de disponibilidade simultânea dos serviços.
* **Manutenção e evolução facilitadas**: componentes bem definidos e independentes permitem evolução incremental.

---

## Tecnologias Utilizadas

* **Python 3.11+**
* **Flask & Flask-RESTful**
* **Flask-SocketIO**
* **Celery**
* **Redis** (broker, cache e Pub/Sub)
* **Pydantic**
* **Docker & Docker Compose**
* **Gunicorn** (produção)

---

## Como rodar localmente

### 1. Pré-requisitos
- Python 3.11+
- pip
- Redis (local ou em container)

### 2. Instalação

```bash
# Crie e ative o ambiente virtual
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instale as dependências
pip install --upgrade pip
pip install -r requirements.txt

# (Opcional) Dê permissão à pasta de logs
chmod -R 777 logs
```

### 3. Configuração

1. Copie o arquivo `.env.example` para `.env` e ajuste as variáveis conforme necessário.
2. Certifique-se de que o Redis está rodando e acessível.

### 4. Executando o servidor

```bash
python run.py
```
O backend estará disponível em [http://localhost:5000](http://localhost:5000)

---

## Como fazer deploy

### 1. Usando Docker

```bash
# Build da imagem
docker build -t nexa-backend .

# Rodar em modo desenvolvimento
docker run -it --rm --env-file .env -p 5000:5000 -v $(pwd):/app nexa-backend python run.py

# Rodar em modo produção (Gunicorn)
docker run -it --rm --env-file .env -p 5000:5000 nexa-backend
```

### 2. Usando Docker Compose

```bash
docker compose up -d --build
```

Para logs e gerenciamento:
```bash
docker compose logs -f
docker compose stop
docker compose down
docker compose start
```

---

## Estrutura do Projeto

```
.
├── app/               # Código principal do backend
├── requirements.txt
├── run.py
├── Dockerfile
├── docker-compose.yml
├── README.md
└── docs/
	├── api.md
	└── ai_server_integration.md
```

---

## Por que escolher o Nexa API?

- Arquitetura robusta, moderna e escalável
- Integração transparente com IA e sistemas legados
- Foco em experiência do usuário e confiabilidade
- Documentação clara e exemplos práticos
- Pronto para produção e evolução contínua

---

> **Nexa API: conectando inteligência, performance e experiência em um só backend.**

