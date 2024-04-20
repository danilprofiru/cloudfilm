from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
import uuid 

# Создаем базовый класс для моделей
Base = declarative_base()

# Модель User
class User(Base):
    __tablename__ = 'User'  # Имя таблицы в базе данных

    userid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(100), nullable=False)  # Имя пользователя
    email = Column(String(255), unique=True, nullable=False)

    # Связь с моделью Auth (one-to-one)
    auth = relationship('Auth', back_populates='user', uselist=False, primaryjoin="User.email == Auth.email")


    def __repr__(self):
        return f"<User(name={self.name}, email={self.email})>"

# Модель Auth
class Auth(Base):
    __tablename__ = 'auth'  # Имя таблицы в базе данных

    authid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)  # Уникальный идентификатор
    email = Column(String(255), ForeignKey('User.email'), nullable=False)  # Внешний ключ к User.email
    password = Column(String(255), nullable=False)  # Хэшированный пароль

    # Связь с моделью User (один-к-одному)
    user = relationship('User', back_populates='auth', uselist=False, primaryjoin="User.email == Auth.email")


    def __repr__(self):
        return f"<Auth(email={self.email})>"