from app.extensions import db, bcrypt
from app.models.models import Role, User


class UserService:
    def __init__(self):
        self.db_session = db.session
        pass

    def get_by_id(self, user_id: int):
        return User.query.get(user_id)

    def get_by_email(self, email: str):
        return User.query.filter_by(email=email).first()

    def create(self, name: str, email: str, password: str, role_name: str = "USER", admin_id: int = None):
        if self.get_by_email(email):
            raise ValueError("Email already exists")

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            raise ValueError("Role does not exist")

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password_hash=password_hash, role_id=role.id, admin_id=admin_id)
        db.session.add(new_user)
        db.session.commit()
        return new_user
    
    def verify_password(self, user: User, password: str) -> bool:
        """Verify a password against the user's hashed password."""
        return bcrypt.check_password_hash(user.password_hash, password)

    def update_user(self, user_id: int, **kwargs):
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db.session.commit()
        return user

    def delete_user(self, user_id: int):
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        db.session.delete(user)
        db.session.commit()