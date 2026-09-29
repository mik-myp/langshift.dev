from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

from app import app, tasks


class RemainingReport(BaseModel):
    model_config = ConfigDict(strict=True)
    count: int = Field(ge=0)
    minutes: int = Field(ge=0)


@app.get("/reports/remaining", response_model=RemainingReport)
def remaining_report(max_minutes: int = Query(default=60, ge=0)):
    selected = [task for task in tasks.values()
                if not task.done and task.minutes <= max_minutes]
    return {"count": len(selected), "minutes": sum(task.minutes for task in selected)}
