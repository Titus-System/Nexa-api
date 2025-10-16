import pdfplumber
import io
import re

def extract_part_numbers(pdf_bytes):
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"

    # -----------------------------
    # Isola apenas a tabela de itens
    # -----------------------------
    match = re.search(r"Line No\..*?Total Amount", text, re.S)
    if match:
        table_text = match.group(0)
    else:
        table_text = text  # fallback

    lines = table_text.splitlines()
    part_numbers = []
    seen = set()

    # -----------------------------
    # Extrai PNs com prefixo 'PN:'
    # -----------------------------
    pn_with_prefix_pattern = re.compile(r"PN:([A-Z0-9.\-]+)")
    lines_without_prefix = []

    for line in lines:
        matches = pn_with_prefix_pattern.findall(line)
        if matches:
            for pn in matches:
                if pn not in seen:
                    seen.add(pn)
                    part_numbers.append(pn)
        else:
            lines_without_prefix.append(line)

    # -----------------------------
    # Extrai PNs sem prefixo nas linhas restantes
    # -----------------------------
    pn_without_prefix_pattern = re.compile(r"-\s*([A-Z0-9.\-]{4,})\b")

    invalid_terms = {
        "CAP", "RES", "REG", "DIODO", "CRISTAL", "TRANS",
        "SMD", "TENSAO", "OSC", "PROTECT", "CHANNEL", "RETIFICADOR",
        "SCHOTTKY", "FET", "CER", "ELE", "LDO"
    }

    for line in lines_without_prefix:
        matches = pn_without_prefix_pattern.findall(line)
        for pn in matches:
            if pn not in seen and pn not in invalid_terms:
                seen.add(pn)
                part_numbers.append(pn)

    # -----------------------------
    # Ordena conforme o texto original (só dentro da tabela)
    # -----------------------------
    ordered = []
    for pn in re.findall(r"[A-Z0-9.\-]{4,}", table_text):
        if pn in seen and pn not in ordered:
            ordered.append(pn)

    return ordered