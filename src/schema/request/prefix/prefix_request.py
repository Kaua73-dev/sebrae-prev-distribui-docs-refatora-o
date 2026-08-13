from pydantic import BaseModel, Field



class PrefixRequest(BaseModel): 
    prefix_name: str = Field(..., min_length=2, max_length=3)