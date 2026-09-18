"""Alerts CRUD and input validation at the API boundary."""


def test_create_list_and_delete(client, team):
    created = client.post(
        "/api/alerts", json={"team_id": team.id, "threshold": 80, "email": "ops@example.com"}
    )
    assert created.status_code == 200
    alert_id = created.json()["id"]
    assert created.json()["enabled"] is True

    listed = client.get(f"/api/alerts?team_id={team.id}").json()
    assert [a["id"] for a in listed] == [alert_id]

    assert client.delete(f"/api/alerts/{alert_id}").status_code == 204
    assert client.get(f"/api/alerts?team_id={team.id}").json() == []


def test_create_for_unknown_team_is_404(client):
    res = client.post(
        "/api/alerts", json={"team_id": 999, "threshold": 80, "email": "ops@example.com"}
    )
    assert res.status_code == 404


def test_delete_unknown_alert_is_404(client):
    assert client.delete("/api/alerts/999").status_code == 404


def test_list_filters_by_team(client, db, team):
    from app.entities import Team

    other = Team(name="data")
    db.add(other)
    db.commit()
    db.refresh(other)

    for tid, email in ((team.id, "a@example.com"), (other.id, "b@example.com")):
        client.post("/api/alerts", json={"team_id": tid, "threshold": 80, "email": email})

    assert len(client.get(f"/api/alerts?team_id={team.id}").json()) == 1
    assert len(client.get("/api/alerts").json()) == 2


def test_malformed_email_is_rejected(client, team):
    res = client.post(
        "/api/alerts", json={"team_id": team.id, "threshold": 80, "email": "not-an-email"}
    )
    assert res.status_code == 422


def test_non_positive_threshold_is_rejected(client, team):
    """A 0% threshold would fire on every evaluation, forever."""
    res = client.post(
        "/api/alerts", json={"team_id": team.id, "threshold": 0, "email": "ops@example.com"}
    )
    assert res.status_code == 422
