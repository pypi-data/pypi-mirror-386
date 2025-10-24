import pytest
from tinystream import Stream

import owasp_dt
from owasp_dt.api.team import get_teams, create_team, delete_team
from owasp_dt.models import Team

test_team = Team(
    uuid="",
    name="test-team",
)

def test_create_team(client: owasp_dt.Client):
    global test_team
    resp = create_team.sync_detailed(client=client, body=test_team)
    assert resp.status_code == 201
    test_team = resp.parsed

@pytest.mark.depends(on=["test_create_team"])
def test_created_team(client: owasp_dt.Client):
    teams = get_teams.sync(client=client)
    assert Stream(teams).filter(lambda team: team.name == "test-team").count() == 1


@pytest.mark.depends(on=["test_created_team"])
def test_delete_team(client: owasp_dt.Client):
    resp = delete_team.sync_detailed(client=client, body=test_team)
    assert resp.status_code == 204

@pytest.mark.depends(on=["test_delete_team"])
def test_deleted_team(client: owasp_dt.Client):
    teams = get_teams.sync(client=client)
    assert Stream(teams).filter(lambda team: team.name == "test-team").count() == 0
