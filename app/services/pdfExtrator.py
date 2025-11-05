from pdfplumber.pdf import PDF

from app.pdf_parsers import PdfParser, PedidoCompraParser, MouserInvoiceParser
from app.pdf_parsers.xwork_invoice_parser import XWorkInvoiceParser


class PdfParserFactory:
    def __init__(self, pdf_file: PDF, supplier:str|None = None):
        self.pdf_file = pdf_file
        self.supplier = supplier
        return
    

    def get_parser(self) -> PdfParser:
        if self.supplier is None:
            return PedidoCompraParser(self.pdf_file)
        
        match self.supplier:
            case "mouser":
                return MouserInvoiceParser(self.pdf_file)
            case "pedido_compra":
                return PedidoCompraParser(self.pdf_file)
            case "xworksolutions":
                return XWorkInvoiceParser(self.pdf_file)
            case _:
                return PedidoCompraParser(self.pdf_file)


    def extract_partnumbers(self):
        parser = self.get_parser()
        return parser.extract_partnumbers()
    