from sqlalchemy.orm import Session
from src.model.prefix import Prefix


class PrefixRepository:
    
    
    def __init__(self, db: Session):
        self.db = db
        
        
    def find_all(self) -> list[Prefix]:
        return self.db.query(Prefix).all()
    
    def save(self, prefix: Prefix) -> Prefix:
        self.db.add(prefix)
        self.db.commit()
        self.db.refresh(prefix)
        return prefix
    
    def find_by_required_prefix_true_order_by_name(self) -> list[Prefix]:
        return (
        self.db.query(Prefix)
        .filter(Prefix.required_prefix == True)
        .order_by(Prefix.prefix_name.asc())
        .all()
    )   
        
    def find_by_prefix_name(self, prefix_name: str) -> Prefix | None:
        return (
        self.db.query(Prefix)
        .filter(Prefix.prefix_name == prefix_name)
        .first()
    )   