from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from analyser.AnalyzerPipeline import SentimentAnalyzer

app = FastAPI() 

sentiment_analyzer = SentimentAnalyzer(
    ru_anchors_path='sentiment_anchors_ru.json', 
    en_anchors_path='anchors.json'
)

@app.get("/health")
def health_check():
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

    analyzed_result = sentiment_analyzer.smart_analyze(feedback.text)

    return {
        "source_id": feedback.source_id,
        "external_id": feedback.external_id,
        "status": "success",
        "analysis": analyzed_result
    }
    
    
