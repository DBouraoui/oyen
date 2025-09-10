from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.dialects.mysql import JSON

from database import Base
from urls.models import Url

class PingResponse(Base):
    __tablename__ = "pingResponse"

    id = Column(Integer, primary_key=True)
    url = Column(ForeignKey(Url.id), nullable=False)
    response = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False)