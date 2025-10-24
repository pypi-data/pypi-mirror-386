[![PyPI version](https://badge.fury.io/py/owasp-dependency-track-client.svg)](https://badge.fury.io/py/owasp-dependency-track-client)

# OWASP Dependency Track Python API client

This is a generated library based on the official OWASP Dependency Track OpenAPI spec (`/api/openapi.json`) using [openapi-python-client](https://github.com/openapi-generators/openapi-python-client).

## Usage

```shell
pip install owasp-dependency-track-client
```

Create the client
```python
from owasp_dt import Client

client = Client(
    base_url="http://localhost:8081/api",
    headers={
        "X-Api-Key": "YOUR API KEY"
    },
    verify_ssl=False,
)
```

Call endpoints:
```python
from owasp_dt.api.project import get_projects

projects = get_projects.sync(client=client)
assert len(projects) > 0
```

## More OWASP Dependency Track utils

This library is part of a wider OWASP Dependency Track tool chain:
- OWASP Dependency Track Python API client: https://github.com/mreiche/owasp-dependency-track-python-client
- OWASP Dependency Track CLI: https://github.com/mreiche/owasp-dependency-track-cli
- OWASP Dependency Track Azure DevOps Sync: https://github.com/mreiche/owasp-dependency-track-azure-devops

## Development

### Update the library

1. Install the requirements: `pip install -r requirements.txt`
2. Start a OWASP DT instance locally (like via. Docker-Compose): https://docs.dependencytrack.org/getting-started/deploy-docker/
3. Run `regenerate-api-client.sh`
4. Check if bug https://github.com/openapi-generators/openapi-python-client/issues/1256 is still in effect
5. Publish this library with the API version tag

### Start the test environment
```shell
cd test
podman|docker compose up
```

- Preconfigured user: `admin:admin2`
- Preconfigured API key: see `test/test.env`
