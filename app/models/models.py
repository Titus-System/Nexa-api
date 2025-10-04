from decimal import Decimal
import enum
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Integer, Numeric, Text, String, DateTime, UniqueConstraint, func, Enum
from sqlalchemy.orm import relationship
from app.extensions import db

class TimeStampMixin():
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class ClassificationStatus(enum.Enum):
    ACTIVE = "active"
    REPLACED = "replaced"
    REJECTED = "rejected"


class TaskStatus(enum.Enum):
    STARTED = "started"
    PROCESSING = "processing"
    FAILED = "failed"
    DONE = "done"


class User(db.Model, TimeStampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    jwt_token_hash = Column(String(256))

    # auto-relacionamento
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # quem é o admin desse usuário
    admin = relationship("User", remote_side=[id], back_populates="supervised_users")

    # usuários supervisionados por esse admin
    supervised_users = relationship("User", back_populates="admin", cascade="all, delete-orphan")

    tasks = relationship("Task", back_populates="user")



class Task(db.Model, TimeStampMixin):
    __tablename__ = "tasks"

    id = Column(String(256), primary_key=True)
    job_id = Column(String(256))
    room_id = Column(String(256))
    progress_channel = Column(String(256))
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.STARTED)
    current = Column(Integer)
    total = Column(Integer)
    message = Column(String(256))
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="tasks")
    classifications = relationship("Classification", back_populates="task")


class Manufacturer(db.Model, TimeStampMixin):
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255))
    country = Column(String(100))

    classifications = relationship("Classification", back_populates="manufacturer")

    __table_args__ = (
        UniqueConstraint("name", "country", name="uq_manufacturer_name_country"),
    )


class Partnumber(db.Model, TimeStampMixin):
    __tablename__ = "partnumbers"

    id = Column(Integer, primary_key=True)
    code = Column(String(255), nullable=False, unique=True)

    # best_classification_id = Column(Integer, ForeignKey("classifications.id"))
    classifications = relationship("Classification", back_populates="partnumber")

    @property
    def best_classification(self):
        if not self.classifications:
            return None
        return max(self.classifications, key=lambda c: c.confidence_rate or 0)


class Tipi(db.Model, TimeStampMixin):
    __tablename__ = "tipi"

    id = Column(Integer, primary_key=True)
    ncm = Column(String(10), nullable=False)
    ex = Column(String(4))
    description = Column(Text)
    tax = Column(Numeric(6,2))

    classifications = relationship("Classification", back_populates="tipi")

    __table_args__ = (
        UniqueConstraint("ncm", "ex", name="uq_tipi_ncm_ex"),
    )


class Classification(db.Model, TimeStampMixin):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True)
    partnumber_id = Column(Integer, ForeignKey("partnumbers.id"))
    task_id = Column(String(256), ForeignKey("tasks.id"))
    tipi_id = Column(Integer, ForeignKey("tipi.id"))
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"))
    short_description = Column(String(256))
    long_description = Column(Text)
    status = Column(Enum(ClassificationStatus), default=ClassificationStatus.ACTIVE)
    confidence_rate = Column(Numeric(4,3))  # exemplo: 0.999

    partnumber = relationship("Partnumber", back_populates="classifications")
    task = relationship("Task", back_populates="classifications")
    tipi = relationship("Tipi", back_populates="classifications")
    manufacturer = relationship("Manufacturer", back_populates="classifications")
