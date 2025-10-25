from pathlib import Path

import pytest

from webbed_duck.config import load_config
from webbed_duck.core.compiler import compile_routes
from webbed_duck.core.routes import load_compiled_routes
from webbed_duck.server.app import create_app

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    TestClient = None  # type: ignore


ROUTE_V1 = """+++
id = "hello"
path = "/hello"
[params.name]
type = "str"
required = false
default = "world"
+++

```sql
SELECT 'Hello, ' || {{name}} || '!' AS greeting;
```
"""


ROUTE_V2 = """+++
id = "hello"
path = "/hello"
[params.name]
type = "str"
required = false
default = "Duck"
+++

```sql
SELECT 'Hello again, ' || {{name}} || '!' AS greeting;
```
"""


@pytest.mark.skipif(TestClient is None, reason="fastapi is not available")
def test_reload_routes_reflects_new_compilation(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    build_dir = tmp_path / "build"
    storage_root = tmp_path / "storage"
    src_dir.mkdir()
    storage_root.mkdir()

    (src_dir / "hello.sql.md").write_text(ROUTE_V1, encoding="utf-8")
    compile_routes(src_dir, build_dir)
    routes = load_compiled_routes(build_dir)

    config = load_config(None)
    config.server.storage_root = storage_root

    app = create_app(routes, config)
    assert hasattr(app.state, "reload_routes")

    with TestClient(app) as client:
        response = client.get("/hello")
        assert response.status_code == 200
        assert response.json()["rows"][0]["greeting"] == "Hello, world!"

        # Update the route contract and recompile
        (src_dir / "hello.sql.md").write_text(ROUTE_V2, encoding="utf-8")
        compile_routes(src_dir, build_dir)
        updated_routes = load_compiled_routes(build_dir)

        app.state.reload_routes(updated_routes)

        refreshed = client.get("/hello")
        assert refreshed.status_code == 200
        payload = refreshed.json()
        assert payload["rows"][0]["greeting"] == "Hello again, Duck!"
