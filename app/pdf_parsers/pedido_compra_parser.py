import re
from pdfplumber.pdf import PDF

from .protocols import PdfParser


class PedidoCompraParser(PdfParser):
    def __init__(self, pdf_file: PDF):
        self.pdf_file = pdf_file
        return

    def execute(self):
        return


    def extract_partnumbers(self):
        text = ""
        for page in self.pdf_file.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"

        match = re.search(r"Line No\..*?Total Amount", text, re.S)
        if match:
            table_text = match.group(0)
        else:
            table_text = text  # fallback

        lines = table_text.splitlines()
        part_numbers = []
        seen = set()

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

        ordered = []
        for pn in re.findall(r"[A-Z0-9.\-]{4,}", table_text):
            if pn in seen and pn not in ordered:
                ordered.append(pn)

        return ordered