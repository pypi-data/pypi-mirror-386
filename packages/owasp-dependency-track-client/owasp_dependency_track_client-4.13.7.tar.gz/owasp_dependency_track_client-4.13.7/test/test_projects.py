import pytest

import owasp_dt
import test
from owasp_dt.api.metrics import get_project_current_metrics
from owasp_dt.api.project import get_projects


@pytest.mark.depends(on=['test/test_upload.py::test_upload_sbom'])
def test_search_project_by_name(client: owasp_dt.Client):
    resp = get_projects.sync_detailed(client=client, name=test.project_name)
    projects = resp.parsed
    assert len(projects) > 0
    assert projects[0].uuid is not None
    test.project_uuid = projects[0].uuid

@pytest.mark.depends(on=['test/test_upload.py::test_get_scan_status', 'test_search_project_by_name'])
def test_get_project_metrics(client: owasp_dt.Client):
    resp = get_project_current_metrics.sync_detailed(client=client, uuid=test.project_uuid)
    metrics = resp.parsed
