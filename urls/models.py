import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base

class Url(Base):
    __tablename__ = "url"

    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False)
    info = Column(String(255), nullable=False)
    schedule = Column(Boolean,default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now())