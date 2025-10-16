# 📄 Endpoint: Upload de Pedido (Extração de Part Numbers)

## 🧠 Visão Geral

Esta rota permite que o usuário envie um **arquivo PDF contendo um pedido de compra**.  
O backend processa o PDF **diretamente em memória**, sem salvar o arquivo em disco, e realiza a **extração automática dos Part Numbers (PNs)** dos produtos listados no documento.

Ela é utilizada principalmente para automatizar a identificação de componentes eletrônicos e códigos de produto a partir de pedidos recebidos em formato PDF.

---

## 🔗 URL Padrão

```
POST /upload-pdf
```

### 📦 Tipo de Requisição
`multipart/form-data`

---

## 📥 O que a rota espera receber

A rota espera um **arquivo PDF** enviado através do campo `pedido`.

| Campo   | Tipo  | Obrigatório | Descrição |
|----------|-------|-------------|------------|
| `pedido` | `File (.pdf)` | ✅ | Arquivo PDF contendo o pedido de compra. |

Exemplo de envio via **Postman** ou **Insomnia**:

- Método: `POST`
- URL: `http://localhost:5000/upload-pdf`
- Body → `form-data`
  - **Key:** `pedido`  
  - **Type:** `File`  
  - **Value:** `pedido_de_compra.pdf`

---

## ⚙️ Etapas de Processamento

1. **Recebimento do arquivo:**  
   O endpoint valida se um arquivo foi enviado e se a extensão é `.pdf`.  
   Caso contrário, retorna um erro 400.

2. **Leitura em memória:**  
   O conteúdo do PDF é carregado diretamente na memória do servidor (`file.read()`), sem salvar ou gerar arquivos temporários no sistema.

3. **Extração de texto com `pdfplumber`:**  
   A função `extract_part_numbers(pdf_bytes)` é chamada.  
   Ela:
   - Abre o PDF usando `pdfplumber` a partir de um *stream* de bytes;
   - Extrai o texto de todas as páginas;
   - Localiza a **tabela de itens** no arquivo;
   - Identifica Part Numbers por dois padrões:
     - **Com prefixo:** `PN:XXXXXX`
     - **Sem prefixo:** `- XXXX` (seguindo regras específicas de filtragem para evitar falsos positivos);
   - Remove duplicados e ordena os PNs conforme aparecem no texto original.

4. **Geração da resposta:**  
   A lista de Part Numbers extraídos é enviada de volta ao cliente em formato JSON.

---

## 📤 Resposta (Saída)

### ✅ Em caso de sucesso (`HTTP 200`)
```json
{
  "message": "Arquivo processado com sucesso!",
  "part_numbers": [
    "12.237",
    "LM358N",
    "74HC595",
    "TL072",
    "BC337"
  ],
  "total": 5
}
```

| Campo | Tipo | Descrição |
|--------|------|-----------|
| `message` | `string` | Mensagem de sucesso. |
| `part_numbers` | `array` | Lista dos PNs encontrados no PDF. |
| `total` | `integer` | Quantidade total de PNs identificados. |

---

### ⚠️ Em caso de erro

| Código | Causa | Exemplo de Retorno |
|--------|--------|--------------------|
| `400` | Nenhum arquivo enviado, nome vazio ou formato inválido | `{ "message": "Nenhum arquivo enviado." }` |
| `500` | Erro interno no processamento do PDF | `{ "error": "Erro ao processar PDF: ..." }` |

---

## 🧾 Exemplo de Requisição e Resposta

### **Entrada**
Requisição enviada via `POST /upload-pdf`:

| Campo | Tipo | Valor |
|--------|------|--------|
| `pedido` | Arquivo PDF | `pedido_cliente_123.pdf` |

### **Saída**
```json
{
  "message": "Arquivo processado com sucesso!",
  "part_numbers": [
    "PN:74HC595",
    "PN:LM358N",
    "12.237"
  ],
  "total": 3
}
```

---

## 🧩 Resumo

- **Framework:** Flask + Flask-RESTful  
- **Leitura:** Em memória
- **Biblioteca de extração:** `pdfplumber`  
- **Regex de busca:** identifica padrões “PN:” e códigos alfanuméricos maiores que 4 caracteres  
- **Saída:** JSON estruturado contendo todos os PNs únicos encontrados  
