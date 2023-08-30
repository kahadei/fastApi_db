from sqlalchemy.orm import relationship

from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class ToDo(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("Users", back_populates="todos")


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    second_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    phone_num = Column(String)
    role = Column(String)

    address_id = Column(Integer, ForeignKey('address.id'), nullable=True)

    todos = relationship('ToDo', back_populates='owner')
    address = relationship("Address", back_populates='user_address')


class Address(Base):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True, index=True)
    address1 = Column(String)
    address2 = Column(String)
    city = Column(String)
    state = Column(String)
    country = Column(String)
    postal_code = Column(String)
    appart_num = Column(Integer)

    user_address = relationship("Users", back_populates="address")
