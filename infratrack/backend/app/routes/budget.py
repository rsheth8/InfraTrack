from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_session
from app.entities import Budget
from app.models import BudgetResponse

router = APIRouter()


@router.get("/budget", response_model=BudgetResponse)
def get_budget(
    team_id: int = Query(..., ge=1),
    db: Session = Depends(get_session),
) -> BudgetResponse:
    current_month = date.today().strftime("%Y-%m")
    row = (
        db.query(Budget)
        .filter(Budget.team_id == team_id, Budget.month == current_month)
        .first()
    )
    if row is None:
        row = (
            db.query(Budget)
            .filter(Budget.team_id == team_id)
            .order_by(Budget.month.desc())
            .first()
        )
    if row is None:
        raise HTTPException(status_code=404, detail="No budget configured for team")

    budget_usd = float(row.budget_usd)
    spend_usd = float(row.spend_usd)
    percent = round((spend_usd / budget_usd) * 100, 2) if budget_usd > 0 else 0.0

    return BudgetResponse(
        team_id=team_id,
        month=row.month,
        budget_usd=budget_usd,
        spend_usd=spend_usd,
        percent_used=percent,
    )
