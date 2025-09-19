# Nexa Backend

Backend do projeto Nexa, construído com **Flask**, **Flask-RESTful** e **Pydantic Settings**.

---

## Requisitos

- Python 3.11+
- pip
- Docker (opcional)
- Docker Compose (opcional)

---

## 1. Rodando localmente (sem Docker)

### Passo 1: Criar e ativar virtualenv

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
````

### Passo 2: Instalar dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt

chmod -R 777 /logs

```





### Passo 3: Rodar o backend

```bash
python run.py
```

* O backend ficará disponível em [http://localhost:5000](http://localhost:5000)

---

## 2. Rodando com Docker

### Passo 1: Build da imagem

```bash
docker build -t nexa-backend .
```

### Passo 2: Rodar o container

**Modo desenvolvimento (debug ligado):**

```bash
docker run -it --rm --env-file .env -p 5000:5000 -v $(pwd):/app nexa-backend python run.py

```

**Modo produção (Gunicorn):**

```bash
docker run -it --rm --env-file .env -p 5000:5000 nexa-backend

```

> ⚠️ Lembre-se de mapear a porta `-p 5000:5000` para acessar no host.

### Passo 3: Parar o container

* Se estiver em foreground: **Ctrl + C**
* Se estiver em detached (`-d`):

```bash
docker ps              # lista containers em execução
docker stop <container_id>   # ou docker stop <container_name>
```

---

## 3. Rodando com Docker Compose

### Passo 1: Subir containers em background

```bash
docker compose up -d --build
```

### Passo 2: Acessar logs

```bash
docker compose logs -f
```

### Passo 3: Parar containers

```bash
docker compose stop       # apenas para containers
docker compose down       # para containers e remove rede
```

### Passo 4: Reiniciar containers

```bash
docker compose start
```

---

## 4. Endpoints principais

* `GET /` → Healthcheck (`backend está rodando`)
* Outros endpoints seguem o padrão de **resources do Flask-RESTful**.

---

## 5. Observações

* A porta padrão do backend é **5000**.
* Para UTF-8 correto nos retornos, a API já está configurada para **não escapar caracteres especiais**.
* Em produção, recomenda-se rodar com **Gunicorn**.
* Variáveis de configuração ficam no **pydantic-settings** (`settings.py`) e podem ser definidas via `.env`.

---

## 6. Estrutura do projeto

```
.
├── app/               # pacote principal do Flask
├── requirements.txt
├── run.py
├── Dockerfile
├── docker-compose.yml
└── README.md
```

