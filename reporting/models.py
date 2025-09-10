import datetime

from sqlalchemy import Column, INTEGER,  DateTime
from database import Base
from sqlalchemy.dialects.mysql import JSON

class ServerReporting(Base):
    __tablename__ = 'server_reporting'

    id = Column(INTEGER, primary_key=True)
    response = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now())