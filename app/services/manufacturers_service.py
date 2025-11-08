from sqlalchemy import and_, select
from app.extensions import db
from app.models.models import Manufacturer
from sqlalchemy.exc import SQLAlchemyError
from app.core.logger_config import logger

class ManufacturersService:
    def __init__(self):
        self.db_session = db.session
        self.logger = logger

    def create(self, dto: dict) -> Manufacturer:
        """
        Cria um novo registro de fabricante no banco.
        Retorna o objeto persistido.
        """
        try:
            new_manufacturer = Manufacturer(
                name=dto.get("name"),
                address=dto.get("address"),
                country=dto.get("country"),
            )

            self.db_session.add(new_manufacturer)
            self.db_session.commit()
            self.db_session.refresh(new_manufacturer)
            self.logger.info(f"Novo fabricante registrado: {new_manufacturer.id, new_manufacturer.name}")
            return new_manufacturer

        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.info(f"Erro ao inserir fabricante no banco de dados: {e}")


    def get_by_id(self, id):
        stmt = select(Manufacturer).where(Manufacturer.id == id)
        return self.db_session.execute(stmt).scalar_one_or_none()

    def find_or_create(self, name: str, address: str = None, country: str = None) -> Manufacturer | None:
        """
        Tenta encontrar um fabricante com base em combinações progressivas:
        (name + address + country) → (name + country) → (name + address) → (name).
        Se não encontrar, cria um novo registro.
        """
        self.logger.info(f"Buscando fabricante {name} no banco de dados")
        try:
            if not name:
                raise ValueError("O campo 'name' é obrigatório para criar ou encontrar um fabricante.")

            query = self.db_session.query(Manufacturer)

            # Normaliza entradas
            name_norm = name.strip()
            address_norm = address.strip() if address else None
            country_norm = country.strip() if country else None

            # 🔹 1. Busca mais completa
            filters = []
            if name_norm and address_norm and country_norm:
                filters.append(
                    and_(
                        Manufacturer.name.ilike(name_norm),
                        Manufacturer.address.ilike(address_norm),
                        Manufacturer.country.ilike(country_norm),
                    )
                )

            # 🔹 2. Busca com name + country
            if name_norm and country_norm:
                filters.append(
                    and_(
                        Manufacturer.name.ilike(name_norm),
                        Manufacturer.country.ilike(country_norm),
                    )
                )

            # 🔹 3. Busca com name + address
            if name_norm and address_norm:
                filters.append(
                    and_(
                        Manufacturer.name.ilike(name_norm),
                        Manufacturer.address.ilike(address_norm),
                    )
                )

            # 🔹 4. Busca apenas por name
            filters.append(Manufacturer.name.ilike(name_norm))

            # Executa buscas na ordem
            for condition in filters:
                manufacturer = query.filter(condition).first()
                if manufacturer:
                    return manufacturer

            # 🔹 Nenhum encontrado → cria novo registro
            dto = {
                "name" : name_norm,
                "address": address_norm,
                "country": country_norm
            }
            new_manufacturer = self.create(dto)
            self.db_session.commit()
            self.db_session.refresh(new_manufacturer)
            return new_manufacturer
        except Exception as e:
            self.logger.info(f"Erro ao buscar fabricante {name} no banco de dados: {e}")
            return None