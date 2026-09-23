from database import Base
from sqlalchemy import Column, String


class SecretKey(Base):
    __tablename__ = "secret_keys"

    name = Column(String(100), primary_key=True)
    value = Column(String, nullable=False)