# 📘 Documento de Arquitetura – Backend

## 1\. Visão Geral

O backend tem como objetivo **automatizar a classificação de NCM e cálculo de alíquotas** a partir de PDFs de pedidos de compra que contêm partnumbers de produtos tecnológicos. O sistema utiliza **Flask** como framework principal, aproveitando sua flexibilidade e suporte para comunicação em tempo real via **WebSockets**.

O fluxo principal da aplicação segue as etapas abaixo:

1.  O usuário faz login, autenticando-se com tokens JWT.
2.  Faz o upload de um PDF, que é recebido pela API.
3.  A API inicia um processamento em segundo plano, delegando a tarefa para um **worker assíncrono (Celery)**.
4.  O worker extrai os partnumbers do PDF, busca especificações, e classifica o produto no NCM via agentes de IA.
5.  O sistema calcula as alíquotas correspondentes ao NCM.
6.  O resultado é salvo no banco de dados e enviado para a interface do Flask.
7.  O Flask, por sua vez, **emite um evento via WebSocket** para o frontend, enviando o resultado final em tempo real.
8.  O usuário pode alterar informações incorretas e salvar as correções.
9.  O resultado final pode ser exportado em JSON ou Excel.
10. O usuário pode consultar o histórico de todas as suas operações.

O sistema será implementado em uma **arquitetura monolítica modular**, pois essa abordagem equilibra a agilidade de desenvolvimento com a organização, facilitando o trabalho em equipe e a manutenção.

-----

## 2\. Camadas da Aplicação

### Camada de Apresentação (Interface de API & WebSockets)

  * **Framework:** Flask
  * **Responsabilidade:** Receber requisições HTTP (RESTful) e gerenciar a comunicação em tempo real com o frontend via WebSockets.
  * **Características:** Stateless (autenticação via JWT) e documentação da API com ferramentas como `Flassger` ou `apifairy`.

### Camada de Aplicação (Orquestração de Casos de Uso)

  * **Responsabilidade:** Servir como a espinha dorsal do fluxo de trabalho, coordenando a execução das regras de negócio.
  * **Características:** Gerencia a delegação de tarefas para a fila do **Celery** e orquestra a comunicação entre os módulos de domínio.

### Camada de Domínio (Regras de Negócio)

  * **Responsabilidade:** Contém a lógica de negócio central do sistema.
  * **Características:** Define as entidades do sistema (Usuário, Operação, Produto, ClassificaçãoNCM) e a lógica de classificação híbrida (heurísticas + IA).

### Camada de Infraestrutura

  * **Responsabilidade:** Fornecer os serviços de suporte para a aplicação.
  * **Características:** Inclui o **PostgreSQL** para persistência, o **Redis** para mensageria assíncrona, e o **Ollama** para executar os modelos de IA localmente.

-----

## 3\. Módulos da Aplicação

Cada módulo é implementado como um **componente interno do monolito**, projetado segundo o princípio de **Responsabilidade Única**. O objetivo é reduzir o acoplamento e facilitar o desenvolvimento paralelo. O desenvolvimento deve se guiar pelas definições abaixo. O projeto segue Monólito Modular com forte inspiração em:

  - **Single Responsibility Principle (SRP)**: Cada módulo foi definido com uma única responsabilidade clara, evitando sobreposição de funções. Isso garante baixo acoplamento (módulos independentes entre si) e alta coesão (cada módulo focado em uma única tarefa).
  - **Layered Architecture / Clean Architecture**: .
  - **Orchestration Pattern para a IA**:

-----

### 0\. **API Module (Interface de API & WebSockets)**

**Responsabilidade Única:**
Servir como a fachada do sistema, expondo a interface pública (REST e WebSockets) e traduzindo requisições externas para chamadas internas da aplicação.

**Responsabilidades Detalhadas:**

  * Definir e expor endpoints (ex: login, upload, consulta, histórico).
  * Validar dados de entrada.
  * Gerenciar autenticação e autorização via JWT.
  * Receber uploads de PDF e enfileirar a tarefa de processamento no Celery.
  * Gerenciar conexões de WebSocket e emitir eventos para o cliente.

**Tecnologias Sugeridas:**

  * **Framework:** Flask
  * **Validação:** `Flask-WTF` ou `Marshmallow`
  * **Mensageria:**  `Celery` (Processamento assíncrono), `Redis`(Broker)
  * **WebSockets:** `Flask-SocketIO` e `eventlet` ou `gevent`
  * **Autenticação:** `Flask-JWT-Extended`

**Atributos adicionais:**

  * **Padronização:** As rotas seguem convenções REST.
  * **Acessibilidade:** A comunicação em tempo real reduz a latência percebida pelo usuário.
  * **Segurança:** Requisições autenticadas por padrão, exceto rotas públicas.

-----

### 1\. **Auth Module**

**Responsabilidade Única**:
Gerenciar autenticação e autorização de usuários.

**Responsabilidades Detalhadas (Funcionalidades)**:

  * Registro e login/logout de usuários.
  * Geração e validação de tokens JWT.
  * Armazenamento seguro de credenciais (hash de senhas).
  * Endpoints: `/login`, `/register`, `/logout`.

**Tecnologias Sugeridas**:

  * **Banco**: PostgreSQL.
  * **Autenticação**: `Flask-JWT-Extended`.
  * **Segurança**: `bcrypt` para hashing.

**Atributos adicionais**:

  * **Escalabilidade**: Stateless (tokens não armazenados em sessão).
  * **Auditabilidade**: Registra tentativas de login mal-sucedidas.

-----

### 2\. **Upload & Extraction Module**

**Responsabilidade Única**:
Gerenciar o upload de PDFs e extrair dados relevantes (texto, partnumbers).

**Responsabilidades Detalhadas**:

  * Receber upload de arquivos do Flask.
  * **Tarefa Celery** para extração de texto com bibliotecas de parsing.
  * Normalização inicial (remoção de caracteres especiais, quebra de linhas).
  * Armazenamento temporário em disco ou bucket.

**Tecnologias Sugeridas**:

  * **Upload**: Flask.
  * **Parsing PDF**: `PyMuPDF` ou `pdfminer.six`.
  * **Armazenamento temporário**: sistema de arquivos local ou MinIO (compatível com S3).

**Atributos adicionais**:

  * **Resiliência**: deve suportar PDFs corrompidos sem travar o pipeline.

-----

### 3\. **AI Orchestration Module**

**Responsabilidade Única**:
Orquestrar agentes de IA especializados para diferentes tarefas.

**Responsabilidades Detalhadas**:

  * Gerenciar ciclo de execução de agentes SmolAgents.
  * Definir ordem de chamadas: buscar especificações, normalizar, classificar.
  * Repassar resultados entre agentes.
  * Consolidar saídas em formato padronizado para o **Classification Module**.

**Tecnologias Sugeridas**:

  * **Agentes**: SmolAgents.
  * **LLM**: Ollama rodando localmente.
  * **Protocolo interno**: JSON padronizado entre agentes.

**Atributos adicionais**:

  * **Extensibilidade**: novos agentes podem ser plugados sem alterar o restante do sistema.

-----

### 4\. **Classification Module**

**Responsabilidade Única**:
Aplicar regras de negócio para classificar produtos em códigos NCM.

**Responsabilidades Detalhadas**:

  * Regras heurísticas (regex, keywords).
  * Classificação semântica via embeddings.
  * Consulta em base de NCM armazenada em Postgres.
  * Combinação das evidências (IA + heurísticas + base).
  * Retorno do NCM mais provável + score de confiança.

**Tecnologias Sugeridas**:

  * **NLP**: Ollama (embeddings).
  * **Heurísticas**: Regex (módulo `re`).
  * **Banco**: PostgreSQL com tabela NCM.
  * **Busca Vetorial**: FAISS ou `pgvector` (plugin Postgres).

**Atributos adicionais**:

  * **Confiabilidade**: deve registrar todas as evidências que justificaram a classificação.

-----

### 5\. **Taxation Module**

**Responsabilidade Única**:
Determinar alíquotas e tributos aplicáveis a partir do NCM classificado.

**Responsabilidades Detalhadas**:

  * Consultar tabela TIPI (Postgres).
  * Associar NCM → Alíquota correta.
  * Tratar exceções (regimes especiais, isenções).

**Tecnologias Sugeridas**:

  * **Banco**: PostgreSQL.
  * **Regras adicionais**: camada de negócio implementada em Python.

**Atributos adicionais**:

  * **Atualizável**: a tabela TIPI deve permitir updates periódicos com facilidade.

-----

### 6\. **Reporting Module**

**Responsabilidade Única**:
Gerar relatórios consolidados de classificação.

**Responsabilidades Detalhadas**:

  * Geração de arquivos Excel com `pandas` + `openpyxl`.
  * Exportação para download via API.

**Tecnologias Sugeridas**:

  * **Relatórios**: `pandas`, `openpyxl`.
  * **Exportação**: Endpoints Flask para download de arquivos.

**Atributos adicionais**:

  * **Padronização**: relatórios devem seguir template fixo.

-----

### 7\. **History & Audit Module**

**Responsabilidade Única**:
Registrar e disponibilizar histórico/auditoria das classificações.

**Responsabilidades Detalhadas**:

  * Registro automático das operações realizadas.
  * Armazenar operações vinculadas ao usuário.
  * Guardar metadados (partnumber, NCM, score, evidências).
  * Fornecer consultas históricas.

**Tecnologias Sugeridas**:

  * **Banco**: PostgreSQL.
  * **Consulta**: SQL + APIs REST.

**Atributos adicionais**:

  * **Auditabilidade**: registros imutáveis (sem deleção).

-----

### 8\. **Logging & Metrics Module**

**Responsabilidade Única**:
Gerar logs estruturados e métricas de monitoramento.

**Responsabilidades Detalhadas**:

  * Logging JSON com `structlog`.

  * Exposição de métricas no padrão Prometheus.

  * Integração com Grafana para dashboards.

  * KPIs principais:

      * Tempo de processamento por operação.
      * Volume de classificações por usuário.
      * Score médio de confiança.
      * Taxa de erros/falhas.

**Tecnologias Sugeridas**:

  * **Logging**: Python `logging` + `structlog`.
  * **Métricas**: Prometheus + Grafana.

**Atributos adicionais**:

  * **Observabilidade**: cada operação deve ser rastreável ponta a ponta.

-----

## 4\. Comunicação entre Módulos

  * **Interna (dentro do monólito):**

      * Via chamadas diretas de função (baixa latência).
      * Camada de aplicação (agora um **worker Celery**) chama módulos de domínio e infraestrutura.

  * **Externa:**

      * Cliente → API REST (Flask).
      * Cliente → WebSockets (Flask-SocketIO).
      * **Flask (app principal) → Redis (Celery Broker)**.
      * **Worker Celery → WebSockets (para enviar resultados)**.
      * Worker Celery → Ollama (via HTTP local API).
      * Worker Celery → Postgres (via SQLAlchemy ORM).

-----

## 5\. Dependências entre Módulos

  * **Auth Module** → Postgres.
  * **Upload & Extraction** → Infraestrutura de arquivos.
  * **AI Orchestration** → SmolAgents, Ollama.
  * **Classification** → AI Orchestration + Base NCM em Postgres.
  * **Taxation** → Classification + Tabelas TIPI (Postgres).
  * **Reporting** → Classification + Taxation + Infraestrutura Excel.
  * **History & Audit** → Todos os outros (precisa de logs/DB).
  * **Logging & Metrics** → Transversal a todos os módulos.
  * **Mensageria (Celery)** → Depende de todos os módulos de processamento.
  * **WebSockets (Flask-SocketIO)** → Depende do worker Celery para receber os resultados e enviar ao frontend.

-----

## 6\. Mapeamento de Tecnologia por Módulo

| Módulo              | Tecnologia / Biblioteca                 |
| :------------------ | :-------------------------------------- |
| Auth                | Flask-JWT-Extended, SQLAlchemy          |
| Upload & Extraction | Flask, PyMuPDF, pdfminer.six            |
| AI Orchestration    | SmolAgents, Ollama (HTTP API local)     |
| Classification      | Regex, heurísticas, Ollama embeddings   |
| Taxation            | Postgres (tabelas TIPI/NCM), SQLAlchemy |
| Reporting           | pandas, openpyxl                        |
| History & Audit     | SQLAlchemy, Postgres                    |
| Logging & Metrics   | structlog, Prometheus, Grafana, Loki    |

-----

## 7\. Tecnologias e Infraestrutura

| Categoria                     | Tecnologia / Ferramenta                                   |
| :---------------------------- | :-------------------------------------------------------- |
| **Linguagem**                 | Python                                                    |
| **Framework API**             | **Flask**                                                 |
| **Mensageria**                | **Celery** (Processamento assíncrono), **Redis** (Broker) |
| **Comunicação em Tempo Real** | **Flask-SocketIO**, `eventlet`                            |
| **Banco de Dados**            | PostgreSQL, SQLAlchemy (ORM)                              |
| **IA Local**                  | **Ollama** (para modelos LLM e embeddings)                |
| **Armazenamento**             | Disco local (dev), MinIO ou S3 (prod)                     |
| **Relatórios**                | `pandas`, `openpyxl`                                      |
| **Observabilidade**           | `structlog`, Prometheus, Grafana                          |
| **Containerização**           | Docker, Docker-compose                                    |

-----

## 8\. Logger e Métricas

  * **Logger:**

      * Formato JSON.
      * Níveis: INFO (operações normais), WARN (classificação incerta), ERROR (falhas).
      * Inclui correlação por `operation_id` para rastrear todo o fluxo.

  * **Métricas (Prometheus):**

      * `operation_processing_time_seconds` (histogram).
      * `ncm_classification_confidence` (gauge).
      * `user_operations_total` (counter).
      * `pdf_upload_errors_total` (counter).

-----

## 9\. Considerações de Projeto

  * **Monólito modular:** Facilita o desenvolvimento em equipe, permitindo que os módulos sejam trabalhados de forma independente.
  * **Baixo acoplamento e alta coesão:** módulos especializados, comunicação bem definida.
  * **Stateless:** API não guarda sessão em memória; autenticação via JWT.
  * **Performance:** **O fluxo de processamento de PDFs agora é completamente assíncrono via Celery**, melhorando a experiência do usuário e a resiliência do sistema.
  * **Segurança:**
      * Senhas hash com bcrypt.
      * JWT tokens expiram.
      * Sanitização de inputs.
  * **Confiabilidade:** logs + auditoria para rastreabilidade fiscal.

-----

## Estrutura de diretórios
```
.
├── app/
│   ├── __init__.py             # App Factory - Monta a aplicação e os módulos
│   ├── config.py               # Configurações globais
│   ├── extensions.py           # Instâncias de extensões (db, jwt, socketio)
│   ├── celery_utils.py         # Configuração do Celery
│   ├── models.py               # Modelos de dados do SQLAlchemy
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py           # Endpoints: /login, /register
│   │   ├── services.py
│   │   └── schemas.py
│   │
│   ├── upload_extraction/
│   │   ├── __init__.py
│   │   ├── routes.py           # Endpoint: /upload
│   │   ├── tasks.py            # Tarefa Celery para extrair texto
│   │   └── services.py
│   │
│   ├── ai_orchestration/
│   │   ├── __init__.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── document_interpreter_agent.py
│   │   │   ├── product_researcher_agent.py
│   │   │   └── ncm_classifier_agent.py
│   │   ├── tasks.py            # Tarefa Celery que executa o pipeline de IA
│   │   └── services.py         # O serviço "maestro" que coordena os agentes
│   │
│   ├── classification/
│   │   ├── __init__.py
│   │   └── services.py         # Lógica de regras, heurísticas e decisão final
│   │
│   └── history_audit/
│       ├── __init__.py
│       ├── routes.py
│       └── services.py
│
├── run.py                      # Ponto de entrada do servidor web
├── celery_worker.py            # Ponto de entrada do worker Celery
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```


## Entregas por sprint

### Primeira Entrega
  * Receber um partnumber via um endpoint simples (sem PDF).
  * Encontrar a definição e detalhes do produto.
  * Criar agente de busca na web
  * Enviar o resultado json via WebSocket para o frontend.

### Segunda Entrega
  * Extrair partnumbers de arquivo PDF.
  * Encontrar NCM e alíquota correspondentes.
  * Salvar o resultado no banco de dados.

### Terceira Entrega
  * Implementar o sistema de login e autenticação com JWT.
  * Exportar o resultado final para Excel.
  * Permitir que o usuário acesse o histórico de suas operações.


## Diagrama
<!-- ![diagrama](./arquitetura.svg) -->
![diagrama](./arquitetura.png)