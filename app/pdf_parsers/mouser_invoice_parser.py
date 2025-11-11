from typing import Dict
from pdfplumber.pdf import PDF
import pandas as pd
import re

from .protocols import PartnumberInfo, PdfParser


class MouserInvoiceParser(PdfParser):
    def __init__(self, pdf_file: PDF):
        self.pdf_file = pdf_file
        self.regex = re.compile(
            r'/\s*(?P<pn>\S+)\s+(?P<manufacturer>\S+)\s+(?P<desc_erp>[^/]+?)/.*?(?:NCM:(?P<ncm>\d+)).*?COO:(?P<coo>\S+)'
        )
                
        self.headers = [
            "Nº da Linha",
            "Part Number / Descrição",
            "Quant. Ordenada",
            "Quant. Embarcada",
            "Quant. Pendente",
            "Preço Unitário (USD)",
            "Preço Total (USD)"
        ]
    

    def extract_partnumbers(self) -> Dict[str, PartnumberInfo]:
        try:
            partnumbers = {}
            product_data = self.create_dataframe()
            for line in product_data[product_data.columns[1]]:
                match = self.regex.search(line)
                if match:
                    pn = match.group('pn').strip()
                    partnumbers[pn] = PartnumberInfo(
                        partnumber=pn,
                        erp_description=match.group('desc_erp').strip(),
                        manufacturer=match.group('manufacturer').strip(),
                        ncm=match.group('ncm') or match.group('hts'),
                        coo=match.group('coo').strip()
                    )
            return partnumbers

        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            return {}


    def clean_cell(self, cell_text: str | None) -> str:
        if cell_text is None:
            return ""
        return re.sub(r'\s+', ' ', cell_text).strip()


    def create_dataframe(self) -> pd.DataFrame:
        all_products = []
        for page_number, page in enumerate(self.pdf_file.pages):
            tables = page.extract_tables()
            
            for table in tables:
                if not table:
                    continue
                
                header_cell = table[0][0] 
                if header_cell and "Nº da" in header_cell and "Line No." in header_cell:                        
                    data_rows = table[1:]
                    for row in data_rows:
                        cleaned_row = [self.clean_cell(cell) for cell in row]
                        
                        if len(cleaned_row) < 7:
                            continue

                        line_no = cleaned_row[0]
                        description_part = cleaned_row[1]
                        
                        if line_no.isdigit():
                            all_products.append(cleaned_row[:7])
                            
                        elif not line_no and description_part and all_products:
                            all_products[-1][1] += " " + description_part
                            
        df = pd.DataFrame(all_products, columns=self.headers)
        return df
