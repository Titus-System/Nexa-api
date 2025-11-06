from typing import Any, Dict, Optional
from pdfplumber.pdf import PDF
from pdfplumber.page import Page
import re

from app.core.logger_config import logger
from .protocols import PartnumberInfo, PdfParser


class XWorkInvoiceParser(PdfParser):
    def __init__(self, pdf_file: PDF):
        self.pdf_file = pdf_file
        self.pattern = re.compile(
            r"PN:\s*([^\s\n]+)"
            r"\s*DESC:(.*?)"
            r"\s*MFR:\s*([^\n]+)"
            r"\s*.*?COO:\s*([^\n]+)",
            re.DOTALL | re.IGNORECASE
        )
        self.logger = logger
        

    def extract_partnumbers(self) -> Dict[str, PartnumberInfo]:
        """Retorna todos os part numbers extraídos do PDF."""
        try:
            partnumbers = self._find_matches()
            self.logger.info(f"Extração concluída. {len(partnumbers)} itens encontrados.")
            return partnumbers
        except Exception as e:
            self.logger.error(f"Erro inesperado durante a extração: {e}")
            return {}


    def _parse_match(self, match: re.Match) -> PartnumberInfo:
        """Extrai os dados de um 'match' regex em formato estruturado."""
        pn, descr, mfr, coo = match.groups()
        return PartnumberInfo(
            partnumber=pn.strip(),
            erp_description=' '.join(descr.strip().split()).replace("- ", "-"),
            manufacturer=mfr.strip(),
            coo=coo.strip(),
        )


    def _safe_extract_tables(self, page) -> list:
        """Tenta extrair tabelas de uma página, retornando lista vazia em caso de falha."""
        try:
            return page.extract_tables() or []
        except Exception as e:
            self.logger.warning(f"Falha ao extrair tabelas da página: {e}")
            return []


    def _process_block(self, text_block: str, all_items: Dict[str, PartnumberInfo]) -> None:
        """Tenta processar e adicionar um bloco de texto ao dicionário de itens."""
        try:
            match = self.pattern.search(text_block)
            if match:
                item = self._parse_match(match)
                all_items[item.partnumber] = item
        except Exception as e:
            self.logger.warning(f"Erro ao processar bloco de texto: {e}")


    def _find_matches(self) -> Dict[str, PartnumberInfo]:
        """Percorre o PDF, extrai e processa blocos de texto válidos."""
        all_items: Dict[str, PartnumberInfo] = {}
        current_block: Optional[str] = None

        total_pages = len(self.pdf_file.pages)
        self.logger.info(f"Total de páginas: {total_pages}")

        for i, page in enumerate(self.pdf_file.pages, start=1):
            self.logger.info(f"Processando página {i}/{total_pages}")
            current_block = self._process_page(page, current_block, all_items)

        if current_block:
            self._process_block(current_block, all_items)

        self.logger.info(f"Extração concluída. {len(all_items)} itens encontrados.")
        return all_items


    def _process_page(
        self,
        page: Page,
        current_block: Optional[str],
        all_items: Dict[str, PartnumberInfo]
    ) -> Optional[str]:
        """Processa uma página do PDF e retorna o último bloco aberto."""
        tables = self._safe_extract_tables(page)
        if not tables:
            self.logger.debug("Nenhuma tabela encontrada nesta página.")
            return current_block

        for table in tables:
            current_block = self._process_table(table, current_block, all_items)

        return current_block


    def _process_table(
        self,
        table: list,
        current_block: Optional[str],
        all_items: Dict[str, PartnumberInfo]
    ) -> Optional[str]:
        """Processa uma tabela do PDF linha a linha."""
        for row in table:
            if not row or len(row) < 4:
                continue

            description_cell = row[3]
            if not description_cell or description_cell.startswith("Description"):
                continue

            if description_cell.startswith("PN:"):
                if current_block:
                    self._process_block(current_block, all_items)
                current_block = description_cell
            elif current_block:
                current_block += "\n" + description_cell

        return current_block
