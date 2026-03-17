from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

app = FastAPI()     

@app.get("/health")
def helth_check():
    return Response(status_code=200)

class FeedbackData(BaseModel):
    source_id: str
    external_id: str
    text: str
    category: str | None = None
    created_at: datetime
    send_time: datetime | None = None
    meta_data: Dict[str, Any] | None = None

@app.post("/analyse")
def analyse_data(feedback: FeedbackData):
    text_to_analyse = feedback.text
