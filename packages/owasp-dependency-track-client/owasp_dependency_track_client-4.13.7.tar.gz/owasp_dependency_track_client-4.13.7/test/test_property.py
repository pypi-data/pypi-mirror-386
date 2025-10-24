import pytest
from tinystream import Opt

import owasp_dt
import test
from owasp_dt.api.project import get_project
from owasp_dt.models import ProjectPropertyPropertyType, ProjectProperty
from test import api


@pytest.mark.depends(on=['test/test_projects.py::test_search_project_by_name'])
def test_upsert_project_property(client: owasp_dt.Client):
    property = ProjectProperty(
        group_name="owasp-dtrack-python-client",
        property_name="test",
        property_type=ProjectPropertyPropertyType.STRING,
        property_value="set",
        description="Custom property test"
    )
    api.upsert_project_property(client=client, uuid=test.project_uuid, property=property)

    def _filter_property(property:ProjectProperty):
        return property.group_name == "owasp-dtrack-python-client" and property.property_name == "test"

    resp = get_project.sync_detailed(client=client, uuid=test.project_uuid)
    project = resp.parsed
    opt_property = Opt(project).map_key("properties").stream().filter(_filter_property).next()
    assert opt_property.present
    assert opt_property.get().property_value == "set"

    property.property_value = "new_value"
    api.upsert_project_property(client=client, uuid=test.project_uuid, property=property)
    resp = get_project.sync_detailed(client=client, uuid=test.project_uuid)
    project = resp.parsed
    opt_property = Opt(project).map_key("properties").stream().filter(_filter_property).next()
    assert opt_property.present
    assert opt_property.get().property_value == "new_value"
