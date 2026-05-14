from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.entities import Team
from app.models import TeamSummary

router = APIRouter()


@router.get("/teams", response_model=list[TeamSummary])
def list_teams(db: Session = Depends(get_session)) -> list[TeamSummary]:
    rows = db.query(Team).order_by(Team.name).all()
    return [TeamSummary(id=t.id, name=t.name) for t in rows]
