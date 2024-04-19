from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

# Создаем базовый класс для моделей
Base = declarative_base()

# Модель User
class User(Base):
    __tablename__ = 'User'  # Имя таблицы в базе данных

    userid = Column(Integer, primary_key=True, autoincrement=True)  # Уникальный идентификатор пользователя
    name = Column(String(100), nullable=False)  # Имя пользователя
    email = Column(String, unique=True, nullable=False)  # Электронная почта пользователя

    # Связь с моделью Auth (one-to-one)
    auth = relationship('Auth', uselist=False, back_populates='user')

    def __repr__(self):
        return f"<User(name={self.name}, email={self.email})>"

# Модель Auth
class Auth(Base):
    __tablename__ = 'auth'  # Имя таблицы в базе данных

    authid = Column(Integer, primary_key=True)  # Уникальный идентификатор
    userid = Column(Integer, ForeignKey('User.userid'))  # Внешний ключ на User.userid
    email = Column(String, nullable=False)  # Электронная почта
    password = Column(String(200), nullable=False)  # Хэшированный пароль

    # Связь с моделью User (one-to-one)
    user = relationship('User', back_populates='auth')

    def __repr__(self):
        return f"<Auth(email={self.email})>"