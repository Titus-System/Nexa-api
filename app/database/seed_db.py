import ssl
from pandas import DataFrame, read_csv, read_excel
from sqlalchemy import exists, select
from sqlalchemy.exc import SQLAlchemyError

from app.models.models import Manufacturer, Ncm, Tipi, UserRole
from app.extensions import db
from app.core.logger_config import logger
from app.services.role_service import RoleService
from app.services.user_service import UserService

#TODO: Remover essa gambiarra de desativar o SSL depois que o endpoint estiver com o certificado correto
ssl._create_default_https_context = ssl._create_unverified_context


def gera_ncm_df() -> DataFrame:
    """Lê e filtra o CSV de NCMs retornando apenas os que começam com '85'."""
    tabela_ncm_url = "https://balanca.economia.gov.br/balanca/bd/tabelas/NCM.csv"
    # tabela_ncm_url = "NCM.csv"
    logger.info("Baixando tabela NCM...")
    ncm_df = read_csv(tabela_ncm_url, delimiter=";", encoding="latin1", dtype={'CO_NCM': str})
    ncm_df = ncm_df[['CO_NCM', 'NO_NCM_POR', 'NO_NCM_ING']]
    ncm_df = ncm_df[ncm_df['CO_NCM'].str.startswith("85")]
    return ncm_df


def gera_tipi_df() -> DataFrame:
    tabela_tipi_url = "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/legislacao/documentos-e-arquivos/tipi.xlsx"
    logger.info("Baixando tabela tipi...")
    tipi_df = read_excel(tabela_tipi_url, skiprows=7, header=0, dtype={"NCM ":str, "EX":str, "DESCRIÇÃO ":str, "ALÍQUOTA (%)":str})
    logger.info(f"colunas: {tipi_df.columns}")
    tipi_df["NCM "] = tipi_df['NCM '].str.replace(".", "", regex=False)
    tipi_df.loc[tipi_df["NCM "].str.len() == 7, "NCM "] = tipi_df["NCM "] + "0"
    tipi_df = tipi_df[tipi_df["NCM "].str.len() >= 8]
    tipi_df = tipi_df[tipi_df["NCM "].str.startswith("85")]
    tipi_df["EX"] = (
        tipi_df["EX"]
        .fillna("00")
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(2)
    )
    tipi_df["ALÍQUOTA (%)"] = (
        tipi_df["ALÍQUOTA (%)"]
        .replace("NT", 0)
        .fillna(0)
        .astype(str)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )
    logger.info(tipi_df.head())
    logger.info(tipi_df.columns)
    return tipi_df


def seed_ncm():
    """Insere no banco os registros NCM filtrados."""
    try:
        ncm_df = gera_ncm_df()
        if ncm_df.empty:
            logger.warning("Nenhum registro NCM encontrado para importar.")
            return

        logger.info("iniciando registro de NCMs no banco de dados.")
        registers = [
            Ncm(
                code=str(row['CO_NCM']).zfill(8),
                description=row['NO_NCM_POR']
            )
            for _, row in ncm_df.iterrows()
        ]

        db.session.bulk_save_objects(registers)
        db.session.commit()

        logger.info(f"{len(registers)} registros NCM inseridos com sucesso.")

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro de banco ao registrar NCMs: {str(e)}")

    except Exception as e:
        logger.error(f"Erro inesperado ao registrar NCMs: {str(e)}")


def get_ncm_id(ncm: str) -> int | None:
    result = db.session.query(Ncm.id).filter(Ncm.code == ncm).one_or_none()
    if result:
        return result[0]
    return None


def seed_tipi():
    try:
        tipi_df = gera_tipi_df()
        if tipi_df.empty:
            logger.warning("Nenhum registro tipi encontrado para importar.")
            return
        
        registers = []
        missed = 0

        for _, row in tipi_df.iterrows():
            ncm_id = get_ncm_id(row["NCM "])
            if ncm_id is None:
                missed += 1
                continue
            register = Tipi(
                ncm_id = ncm_id,
                ex = row["EX"],
                description = row["DESCRIÇÃO "],
                tax = row["ALÍQUOTA (%)"]
            )
            registers.append(register)
        
        db.session.bulk_save_objects(registers)
        db.session.commit()
        logger.info(f"{len(registers)} registros TIPI inseridos com sucesso. {missed} registros perdidos.")

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro de banco ao registrar na tabela tipi: {str(e)}")

    except Exception as e:
        logger.error(f"Erro inesperado ao registrar na tabela tipi: {str(e)}")


def seed_manufacturers():
    from .manufacturers import manufacturers_list
    manuf = []
    for i in manufacturers_list:
        register = Manufacturer(
            name = i.get("FABRICANTE"),
            address = i.get("ENDERECO"),
            country = i.get("PAIS")
        )
        manuf.append(register)
    db.session.bulk_save_objects(manuf)
    db.session.commit()
    logger.info(f"{len(manuf)} Fabricantes registrados na tabela manufacturers.")


def table_is_empty(table_name:str) -> bool:
    table = db.metadata.tables[table_name]
    stmt = select(exists().where(table.c.id != None)) 
    return not db.session.execute(stmt).scalar()


def seed_db():
    if table_is_empty("ncms"):
        logger.info("Tabela ncms está vazia. Iniciando processo de registro de NCMs...")
        seed_ncm()
    if table_is_empty("tipi"):
        logger.info("Tabela tipi está vazia. Iniciando processo de registro de alíquotas...")
        seed_tipi()
    if table_is_empty("manufacturers"):
        logger.info("Tabela manufacturers está vazia. Iniciando processo de registro de fabricantes...")
        seed_manufacturers()

    role_service = RoleService()
    for role in UserRole:
        role_service.create(name=role.value)

    user_service = UserService()
    user_service.create(
        name="Nexa Tester",
        email="tester@nexa.com",
        password="test1234",
        role_name="ADMIN",
        admin_id=None
    )