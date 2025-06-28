
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="External Test API")

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

@app.get("/")
def read_root():
    return {"message": "Hello from external FastAPI project!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "fastapi-external-test"}

@app.post("/items/")
def create_item(item: Item):
    return {"item": item, "message": "Item created successfully"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
