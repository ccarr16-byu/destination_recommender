from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class SearchQuery(BaseModel):
    query: str

@app.post("/api/search")
async def search(query: SearchQuery):
    try:
        # For now, just print the query and return it
        print(f"User searched for: {query.query}")
        return {"message": f"Received search query: {query.query}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 