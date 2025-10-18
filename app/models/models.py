import enum
from sqlalchemy import (Column, ForeignKey, Integer, Numeric, Text, String, 
                        UniqueConstraint, func, Enum, CheckConstraint,
                        ForeignKeyConstraint)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship
from app.extensions import db

class TimeStampMixin():
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"

class ClassificationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REPLACED = "REPLACED"
    REJECTED = "REJECTED"

class TaskStatus(str, enum.Enum):
    STARTED = "STARTED"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    DONE = "DONE"
    PARTIAL_RESULT = "PARTIAL_RESULT"


role_permissions = db.Table('role_permissions',
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class Role(db.Model):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    
    users = relationship('User', back_populates='role')
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles')


class Permission(db.Model):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')


class User(db.Model, TimeStampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String(128), nullable=False)
    # role = Column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.USER)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    jwt_token_hash = Column(String(256))

    admin_id = Column(Integer, ForeignKey("users.id", ondelete='SET NULL'), nullable=True)

    admin = relationship("User", remote_side=[id], back_populates="supervised_users")
    supervised_users = relationship("User", back_populates="admin")
    classification_tasks = relationship("ClassificationTask", back_populates="user")
    role = relationship('Role', back_populates='users', uselist=False)


class ClassificationTask(db.Model, TimeStampMixin):
    __tablename__ = "classification_tasks"

    id = Column(String(256), primary_key=True)
    job_id = Column(String(256))
    room_id = Column(String(256))
    progress_channel = Column(String(256))
    status = Column(Enum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.STARTED)
    current = Column(Integer)
    total = Column(Integer)
    message = Column(String(256))
    user_id = Column(Integer, ForeignKey("users.id", ondelete='SET NULL'))

    user = relationship("User", back_populates="classification_tasks")
    classifications = relationship("Classification", back_populates="classification_task")


class Manufacturer(db.Model, TimeStampMixin):
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True)
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
    
    best_classification_id = Column(Integer, unique=True, nullable=True)

    classifications = relationship("Classification", 
                                   back_populates="partnumber", 
                                   cascade="all, delete-orphan", 
                                   passive_deletes=True,
                                   foreign_keys="[Classification.partnumber_id]")

    best_classification = relationship("Classification", 
                                       foreign_keys=[best_classification_id], 
                                       post_update=True,
                                       uselist=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['best_classification_id'], 
            ['classifications.id'], 
            name='fk_partnumber_best_classification',
            ondelete='SET NULL',
            use_alter=True,
            deferrable=True, 
            initially='DEFERRED'
        ),
    )

class Ncm(db.Model, TimeStampMixin):
    __tablename__ = "ncms"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, unique=True)
    description = Column(Text, nullable=False)

    tipi_rules = relationship("Tipi", back_populates="ncm", cascade="all, delete-orphan")


class Tipi(db.Model, TimeStampMixin):
    __tablename__ = "tipi"

    id = Column(Integer, primary_key=True)
    ncm_id = Column(Integer, ForeignKey("ncms.id"), nullable=False)
    ex = Column(String(4), nullable=True)
    description = Column(Text)
    tax = Column(Numeric(6, 2))

    classifications = relationship("Classification", back_populates="tipi")
    ncm = relationship("Ncm", back_populates="tipi_rules")

    __table_args__ = (
        UniqueConstraint("ncm_id", "ex", name="uq_tipi_ncm_id_ex"),
    )


class Classification(db.Model, TimeStampMixin):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True)
    partnumber_id = Column(Integer, ForeignKey("partnumbers.id", ondelete='CASCADE'), nullable=False)
    classification_task_id = Column(String(256), ForeignKey("classification_tasks.id", ondelete='SET NULL'))
    tipi_id = Column(Integer, ForeignKey("tipi.id", ondelete='SET NULL'))
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id", ondelete='SET NULL'))
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete='SET NULL'), nullable=False, index=True)
    
    short_description = Column(String(256))
    long_description = Column(Text)
    status = Column(Enum(ClassificationStatus, name="classification_status"), default=ClassificationStatus.ACTIVE)
    confidence_rate = Column(Numeric(4, 3))

    partnumber = relationship("Partnumber", back_populates="classifications", foreign_keys=[partnumber_id])
    classification_task = relationship("ClassificationTask", back_populates="classifications")
    tipi = relationship("Tipi", back_populates="classifications")
    manufacturer = relationship("Manufacturer", back_populates="classifications")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id], uselist=False)

    __table_args__ = (
        CheckConstraint("confidence_rate >= 0 AND confidence_rate <= 1", name="chk_confidence_rate"),
    )