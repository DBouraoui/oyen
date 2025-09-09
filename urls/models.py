import datetime
from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class Ping(Base):
    __tablename__ = "url"

    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False)
    info = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now())