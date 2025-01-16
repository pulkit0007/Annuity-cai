from pydantic import BaseModel
from typing import List

class VectorDataBase(BaseModel):
    """ VectorDataBase """
    fund_id: str
    fund_name: str
    doc_type: str
    genre: str
    text: str
    vector: List[float]

class VectorCreateRequest(BaseModel):
    """ VectorCreateRequest """
    fund_id: str
    fund_name: str
    vector_texts: List[str]

class VectorCreateResponse(BaseModel):
    """ VectorCreateResponse"""
    message: str
    vector_data: VectorDataBase

class VectorReadResponse(VectorDataBase):
    """ VectorReadResponse"""
    id: str
    fund_id: str
    fund_name: str
    doc_type: str
    genre: str
    text: str
    vector: List[float]
