from datetime import datetime

from src.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, DateTime, String

class Prefix(Base):    
    __tablename__ = "prefix"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    prefix_name: Mapped[str] = mapped_column(String(3), unique= True, nullable= False)
    
    required_prefix: Mapped[bool] = mapped_column(Boolean, default= False)
    
    create_at: Mapped[datetime] = mapped_column(DateTime, default= datetime.now)