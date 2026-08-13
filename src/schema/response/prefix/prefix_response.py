from pydantic import BaseModel, ConfigDict
from datetime import datetime

class PrefixResponse(BaseModel):
    prefix_name: str
    required_prefix: bool
    create_at: datetime
    
    model_config = ConfigDict(from_attributes=True)