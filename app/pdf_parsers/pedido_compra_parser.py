import re
from typing import Dict
from pdfplumber.pdf import PDF

from .protocols import PartnumberInfo, PdfParser


class PedidoCompraParser(PdfParser):
    def __init__(self, pdf_file: PDF):
        self.pdf_file = pdf_file

        self.re_with_prefix = re.compile(r"PN:\s*(?P<pn>[A-Z0-9.\-]+)", re.IGNORECASE)
        self.token_re = re.compile(r"\b([A-Z0-9.\-]{4,})\b", re.IGNORECASE)
        self.invalid_terms = {
            "CAP", "RES", "REG", "DIODO", "CRISTAL", "TRANS",
            "SMD", "TENSAO", "OSC", "PROTECT", "CHANNEL", "RETIFICADOR",
            "SCHOTTKY", "FET", "CER", "ELE", "LDO"
        }

    def _is_valid_pn_token(self, token: str) -> bool:
        """Valida token: deve conter pelo menos uma letra e não ser um termo inválido."""
        t = token.strip().upper()
        if t in self.invalid_terms:
            return False
        if not re.search(r"[A-Z]", t):
            return False
        if len(re.sub(r"[^A-Z0-9]", "", t)) < 4:
            return False
        return True

    def extract_partnumbers(self) -> Dict[str, PartnumberInfo]:
        try:
            return self.extract_item_data()
        except Exception as e:
            print(f"Erro ao extrair dados: {e}")
            return {}

    def extract_item_data(self) -> Dict[str, PartnumberInfo]:
        # junta todo o texto
        text = ""
        for page in self.pdf_file.pages:
            page_text = page.extract_text(layout=True) or ""
            text += page_text + "\n"

        m = re.search(r"Line No\..*?Total Amount", text, re.S | re.I)
        table_text = m.group(0) if m else text

        part_data: Dict[str, PartnumberInfo] = {}
        seen = set()

        line_re = re.compile(r"^\s*\d{2}\s+(.+?)\s+(\d{4})\s+(\d{2}/\d{2}/\d{2})", re.S)

        for line in table_text.splitlines():
            
            match = line_re.search(line)
            if not match:
                continue

            full_cell_text = match.group(1).strip()

            tokens = full_cell_text.split(maxsplit=1)
            if len(tokens) < 2:
                continue  

            descr_cell = tokens[1].strip()

            pn = None
            erp_desc = None

            # 1) tenta PN com prefixo "PN:"
            m1 = self.re_with_prefix.search(descr_cell)
            if m1:
                pn_candidate = m1.group("pn").strip()
                # descrição = tudo antes do "PN:"
                erp_desc = descr_cell[:m1.start()].strip()

                if len(pn_candidate) >= 4:
                    pn = pn_candidate.upper()

            if pn is None:
                # 2) se não há PN:, tenta detectar PN no início da célula
                tokens_desc = descr_cell.split()
                if tokens_desc:
                    first = tokens_desc[0].strip(",.;:")
                    if self._is_valid_pn_token(first):
                        pn = first.upper()
                        # descrição: todo o resto (excluindo primeiro token)
                        erp_desc = " ".join(tokens_desc[1:]).strip()
                        if not erp_desc:
                            # se a descrição ficou vazia, use a célula inteira menos o PN
                            erp_desc = descr_cell[len(tokens_desc[0]):].strip()

            if pn is None:
                # 3) procura qualquer token válido dentro da célula (varredura de fallback)
                for tok in self.token_re.findall(descr_cell):
                    tok_clean = tok.strip(",.;:")
                    if self._is_valid_pn_token(tok_clean):
                        pn = tok_clean.upper()
                        # descrição = célula sem o PN encontrado (primeira ocorrência)
                        erp_desc = re.sub(re.escape(tok), "", descr_cell, count=1, flags=re.IGNORECASE).strip()
                        break

            if pn and pn not in seen:
                seen.add(pn)
                if not erp_desc:
                    erp_desc = descr_cell
                erp_desc = re.sub(r"\s{2,}", " ", erp_desc).strip()
                part_data[pn] = PartnumberInfo(partnumber=pn, erp_description=erp_desc)

        return part_data
