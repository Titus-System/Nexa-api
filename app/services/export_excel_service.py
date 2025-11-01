import io
import pandas as pd

from app.core.logger_config import logger
from app.models.models import Classification
from app.services.classification_tasks_service import ClassificationTaskService


class ExportExcelService:
    def __init__(self):
        self.task_service = ClassificationTaskService()
        self.logger = logger

        self.columns = [
            "Seq",
            "DESCRIÇÃO ERP",
            "DESCRIÇÃO PARA DECLARAÇÃO DE IMPORTAÇÃO",
            "NCM (CLASSIFICAÇÃO FISCAL)",
            "FABRICANTE",
            "Endereço",
            "Descr. País"
        ]


    def export_from_task_id(self, task_id:str) -> io.BytesIO:
        raw_data = self.task_service.read(task_id)
        classifications: list[Classification] = raw_data.classifications

        treated_data = []
        seq = 1
        for c in classifications:
            exception = c.tipi.ex if c.tipi.ex != "00" else None
            d = {
                "Seq": seq,
                "DESCRIÇÃO ERP": c.long_description[:30],
                "DESCRIÇÃO PARA DECLARAÇÃO DE IMPORTAÇÃO": c.long_description,
                "NCM (CLASSIFICAÇÃO FISCAL)": f"{c.tipi.ncm.code} ({exception})" if exception else c.tipi.ncm.code,
                "FABRICANTE": c.manufacturer.name,
                "Endereço": c.manufacturer.address,
                "Descr. País": c.manufacturer.country
            }
            treated_data.append(d)
            seq += 1

        df = pd.DataFrame(treated_data, columns=self.columns)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name='Classificacoes')

        output.seek(0)
        return output