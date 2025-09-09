from sqlalchemy.orm import Session
from .models import Ping

class PingService:

    def __init__(self, db: Session):
        self.db = db

    def is_url_exist(self, ping: str) -> bool:
        return self.db.query(Ping).filter(Ping.url == ping).count() > 0

    def get_url_by_id(self, ping_id: int):
        return self.db.query(Ping).filter(Ping.id == ping_id).first()

    def get_all_urls(self):
        return self.db.query(Ping).all()