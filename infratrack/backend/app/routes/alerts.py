from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.entities import Alert, Team
from app.models import AlertCreate, AlertResponse

router = APIRouter()


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(team_id: int | None = None, db: Session = Depends(get_session)):
    q = db.query(Alert)
    if team_id is not None:
        q = q.filter(Alert.team_id == team_id)
    return q.order_by(Alert.id.desc()).all()


@router.post("/alerts", response_model=AlertResponse)
def create_alert(payload: AlertCreate, db: Session = Depends(get_session)) -> AlertResponse:
    if db.get(Team, payload.team_id) is None:
        raise HTTPException(status_code=404, detail="Team not found")

    alert = Alert(
        team_id=payload.team_id,
        threshold=payload.threshold,
        email=payload.email,
        enabled=True,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.delete("/alerts/{alert_id}", status_code=204)
def delete_alert(alert_id: int, db: Session = Depends(get_session)) -> None:
    row = db.get(Alert, alert_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(row)
    db.commit()
