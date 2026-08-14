from pydantic import BaseModel, Field



class PrefixUpdateRequest(BaseModel):
    prefix_name: str = Field(..., min_length=2, max_length=3)
    prefix_required: bool