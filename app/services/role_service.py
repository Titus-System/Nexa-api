from app.models.models import Permission, Role
from app.extensions import db
from app.core.logger_config import logger


class RoleService:
    def __init__(self):
        self.db_session = db.session
        self.logger = logger

    def get_by_id(self, role_id: int):
        return Role.query.get(role_id)

    def get_by_name(self, name: str):
        return Role.query.filter_by(name=name).first()

    def create(self, name: str, permission_names: list = None):
        new_role = self.get_by_name(name)
        if new_role:
            self.logger.info(f"Role de nome '{name}' já existe.")
            return new_role
        
        new_role = Role(name=name)

        if permission_names:
            permissions = Permission.query.filter(Permission.name.in_(permission_names)).all()
            if len(permissions) != len(permission_names):
                raise ValueError("One or more permissions do not exist")
            new_role.permissions = permissions

        self.db_session.add(new_role)
        self.db_session.commit()
        self.logger.info(f"Role '{name}' criada com sucesso.")
        return new_role

    def update_role(self, role_id: int, **kwargs):
        role = self.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found")

        for key, value in kwargs.items():
            if key == "permission_names":
                permissions = Permission.query.filter(Permission.name.in_(value)).all()
                if len(permissions) != len(value):
                    raise ValueError("One or more permissions do not exist")
                role.permissions = permissions
            elif hasattr(role, key):
                setattr(role, key, value)

        self.db_session.commit()
        return role

    def delete_role(self, role_id: int):
        role = self.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found")

        self.db_session.delete(role)
        self.db_session.commit()