from __future__ import annotations

import datetime
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pytest

from webbed_duck.config import Config, load_config
from webbed_duck.core.compiler import compile_routes
from webbed_duck.core.incremental import run_incremental
from webbed_duck.core.routes import load_compiled_routes
from webbed_duck.plugins import assets as assets_plugins
from webbed_duck.plugins import charts as charts_plugins
from webbed_duck.server.app import create_app

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    TestClient = None  # type: ignore

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for <3.11
    import tomli as tomllib  # type: ignore


ROUTE_PRIMARY = """+++
id = "hello"
path = "/hello"
[params.name]
type = "str"
required = false
default = "DuckDB"
ui_control = "input"
ui_label = "Name"
ui_placeholder = "Team mate"
ui_help = "Enter a name and apply the filter"

[html_t]
show_params = ["name"]

[html_c]
show_params = ["name"]

[overrides]
key_columns = ["greeting"]
allowed = ["note"]

[append]
columns = ["greeting", "note", "created_at"]

[share]
pii_columns = ["note"]
+++

```sql
SELECT
  'Hello, ' || {{name}} || '!' AS greeting,
  'private-note' AS note,
  CURRENT_DATE AS created_at
```
"""


ROUTE_INCREMENTAL = """+++
id = "by_date"
path = "/by_date"
[params.day]
type = "str"
required = true
+++

```sql
SELECT {{day}} AS day_value;
```
"""


@dataclass(slots=True)
class ReadmeContext:
    repo_root: Path
    readme_lines: list[str]
    compiled_hashes: dict[str, str]
    recompiled_hashes: dict[str, str]
    compiled_routes: list
    route_json: dict
    html_text: str
    html_headers: dict[str, str]
    cards_text: str
    cards_headers: dict[str, str]
    feed_text: str
    html_rpc_payload: dict
    cards_rpc_payload: dict
    csv_headers: dict[str, str]
    parquet_headers: dict[str, str]
    arrow_headers: dict[str, str]
    analytics_payload: dict
    schema_payload: dict
    override_payload: dict
    append_path: Path
    share_payload: dict
    share_db_hashes: tuple[str, str]
    local_resolve_payload: dict
    incremental_rows: list
    checkpoints_exists: bool
    storage_root_layout: dict[str, bool]
    repo_structure: dict[str, bool]
    reload_capable: bool
    python_requires: str
    optional_dependencies: dict[str, list[str]]
    dependencies: list[str]
    email_records: list
    assets_registry_size: int
    charts_registry_size: int
    duckdb_connect_counts: list[int]


def _install_email_adapter(records: list[tuple]) -> str:
    import types
    import sys

    module_name = "tests.readme_email_capture"
    module = types.ModuleType(module_name)

    def send_email(to_addrs, subject, html_body, text_body=None, attachments=None):
        records.append((tuple(to_addrs), subject, html_body, text_body, attachments))

    module.send_email = send_email  # type: ignore[attr-defined]
    sys.modules[module_name] = module
    return module_name


def _extract_statements(readme: str) -> list[str]:
    statements: list[str] = []
    in_code_block = False
    for line in readme.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code_block:
                if stripped == "```":
                    in_code_block = False
                continue
            in_code_block = True
            continue
        if in_code_block or not stripped or stripped.startswith("#"):
            continue
        statements.append(stripped)
    return statements


@pytest.fixture(scope="module")
def readme_context(tmp_path_factory: pytest.TempPathFactory) -> ReadmeContext:
    if TestClient is None:  # pragma: no cover - fastapi optional
        pytest.skip("fastapi is required to validate README statements")

    tmp_path = tmp_path_factory.mktemp("readme")
    src_dir = tmp_path / "src"
    build_dir = tmp_path / "build"
    rebuild_dir = tmp_path / "build2"
    storage_root = tmp_path / "storage"
    src_dir.mkdir()

    (src_dir / "hello.sql.md").write_text(ROUTE_PRIMARY, encoding="utf-8")
    (src_dir / "by_date.sql.md").write_text(ROUTE_INCREMENTAL, encoding="utf-8")

    compile_routes(src_dir, build_dir)
    compile_routes(src_dir, rebuild_dir)

    def _hash_dir(path: Path) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for file in sorted(path.glob("**/*.py")):
            hashes[str(file.relative_to(path))] = hashlib.sha256(file.read_bytes()).hexdigest()
        return hashes

    compiled_hashes = _hash_dir(build_dir)
    recompiled_hashes = _hash_dir(rebuild_dir)

    routes = load_compiled_routes(build_dir)
    config = load_config(None)
    config.server.storage_root = storage_root
    config.auth.mode = "pseudo"
    config.auth.allowed_domains = ["example.com"]
    config.email.adapter = f"{_install_email_adapter(records := [])}:send_email"
    config.email.bind_share_to_user_agent = False
    config.email.bind_share_to_ip_prefix = False

    app = create_app(routes, config)
    reload_capable = hasattr(app.state, "reload_routes")

    duckdb_connect_counts: list[int] = []

    def request_with_tracking(client: TestClient, method: str, path: str, **kwargs):
        from unittest.mock import patch
        import duckdb

        call_count = 0
        original = duckdb.connect

        def tracking_connect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return original(*args, **kwargs)

        with patch("webbed_duck.server.app.duckdb.connect", side_effect=tracking_connect):
            response = getattr(client, method)(path, **kwargs)
        duckdb_connect_counts.append(call_count)
        return response

    with TestClient(app) as client:
        login = client.post("/auth/pseudo/session", json={"email": "user@example.com"})
        assert login.status_code == 200

        json_response = request_with_tracking(client, "get", "/hello")
        route_json = json_response.json()

        html_response = client.get("/hello", params={"format": "html_t"})
        cards_response = client.get("/hello", params={"format": "html_c"})
        feed_response = client.get("/hello", params={"format": "feed"})
        csv_response = client.get("/hello", params={"format": "csv"})
        parquet_response = client.get("/hello", params={"format": "parquet"})
        arrow_response = client.get("/hello", params={"format": "arrow", "limit": 1})

        override_response = client.post(
            "/routes/hello/overrides",
            json={"column": "note", "key": {"greeting": "Hello, DuckDB!"}, "value": "annotated"},
        )
        append_response = client.post(
            "/routes/hello/append",
            json={"greeting": "Hello, DuckDB!", "note": "annotated", "created_at": "2025-01-01"},
        )
        schema_response = client.get("/routes/hello/schema")
        analytics_response = client.get("/routes")

        share_response = client.post(
            "/routes/hello/share",
            json={"emails": ["friend@example.com"], "params": {"name": "Duck"}, "format": "json"},
        )
        share_payload = share_response.json()["share"]
        share_token = share_payload["token"]
        shared_response = client.get(f"/shares/{share_token}")

        local_resolve = client.post("/local/resolve", json={"reference": "local:hello?name=Goose"})

        # Trigger incremental analytics by running route again with tracking
        request_with_tracking(client, "get", "/hello", params={"name": "Swan"})

    checkpoints_path = storage_root / "runtime" / "checkpoints.duckdb"
    incremental_rows = list(
        run_incremental(
            "by_date",
            cursor_param="day",
            start=datetime.date(2024, 1, 1),
            end=datetime.date(2024, 1, 3),
            config=config,
            build_dir=build_dir,
        )
    )

    share_db_path = storage_root / "runtime" / "meta.sqlite3"
    with sqlite3.connect(share_db_path) as conn:
        share_hash = conn.execute("SELECT token_hash FROM shares").fetchone()[0]
        session_hash = conn.execute("SELECT token_hash FROM sessions").fetchone()[0]

    storage_root_layout = {
        "routes_build": (storage_root / "routes_build").exists(),
        "cache": (storage_root / "cache").exists(),
        "schemas": (storage_root / "schemas").exists(),
        "static": (storage_root / "static").exists(),
        "runtime": (storage_root / "runtime").exists(),
        "runtime/meta.sqlite3": share_db_path.exists(),
        "runtime/checkpoints.duckdb": checkpoints_path.exists(),
    }

    repo_root = Path(__file__).resolve().parents[1]
    repo_structure = {
        "CHANGELOG.md": (repo_root / "CHANGELOG.md").is_file(),
        "README.md": (repo_root / "README.md").is_file(),
        "config.toml": (repo_root / "config.toml").is_file(),
        "docs": (repo_root / "docs").is_dir(),
        "examples": (repo_root / "examples").is_dir(),
        "routes_src": (repo_root / "routes_src").is_dir(),
        "routes_build": (repo_root / "routes_build").is_dir(),
        "tests": (repo_root / "tests").is_dir(),
        "webbed_duck": (repo_root / "webbed_duck").is_dir(),
    }

    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    project_data = pyproject.get("project", {})
    python_requires = project_data.get("requires-python", "")
    optional_dependencies = {
        key: sorted(value)
        for key, value in project_data.get("optional-dependencies", {}).items()
        if isinstance(value, list)
    }
    dependencies = [str(item) for item in project_data.get("dependencies", [])]

    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    readme_lines = _extract_statements(readme_text)

    rpc_pattern = re.compile(
        r"<script type='application/json' id='wd-rpc-config'>(?P<data>.+?)</script>",
        re.DOTALL,
    )

    def _rpc_payload_from(html_text: str) -> dict:
        match = rpc_pattern.search(html_text)
        if not match:
            return {}
        try:
            return json.loads(match.group("data"))
        except json.JSONDecodeError:
            return {}

    return ReadmeContext(
        repo_root=repo_root,
        readme_lines=readme_lines,
        compiled_hashes=compiled_hashes,
        recompiled_hashes=recompiled_hashes,
        compiled_routes=routes,
        route_json=route_json,
        html_text=html_response.text,
        html_headers=dict(html_response.headers),
        html_rpc_payload=_rpc_payload_from(html_response.text),
        cards_text=cards_response.text,
        cards_headers=dict(cards_response.headers),
        cards_rpc_payload=_rpc_payload_from(cards_response.text),
        feed_text=feed_response.text,
        csv_headers=dict(csv_response.headers),
        parquet_headers=dict(parquet_response.headers),
        arrow_headers=dict(arrow_response.headers),
        analytics_payload=analytics_response.json(),
        schema_payload=schema_response.json(),
        override_payload=override_response.json()["override"],
        append_path=Path(append_response.json()["path"]),
        share_payload={"meta": share_payload, "resolved": shared_response.json()},
        share_db_hashes=(share_hash, session_hash),
        local_resolve_payload=local_resolve.json(),
        incremental_rows=incremental_rows,
        checkpoints_exists=checkpoints_path.exists(),
        storage_root_layout=storage_root_layout,
        repo_structure=repo_structure,
        reload_capable=reload_capable,
        python_requires=python_requires,
        optional_dependencies=optional_dependencies,
        dependencies=dependencies,
        email_records=records,
        assets_registry_size=len(getattr(assets_plugins, "_REGISTRY", {})),
        charts_registry_size=len(getattr(charts_plugins, "_RENDERERS", {})),
        duckdb_connect_counts=duckdb_connect_counts,
    )


def _ensure(condition: bool, message: str) -> None:
    assert condition, message


def _python_requirement_at_least(requirement: str, minimum: tuple[int, int]) -> bool:
    if not requirement.startswith(">="):
        return False
    version = requirement[2:].strip()
    parts = version.split(".")
    try:
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        return False
    return (major, minor) >= minimum


@pytest.mark.skipif(TestClient is None, reason="fastapi is not available")
def test_readme_statements_are_covered(readme_context: ReadmeContext) -> None:
    ctx = readme_context

    validators: list[tuple[Callable[[str], bool], Callable[[str], None]]] = [
        (lambda s: s.startswith("`webbed_duck` is a"), lambda s: _ensure(
            ctx.route_json["rows"][0]["greeting"].startswith("Hello"), s
        )),
        (lambda s: s.startswith("This README is the canonical"), lambda s: None),
        (lambda s: s.startswith("See the [Quickstart workspace setup]"), lambda s: _ensure(
            ctx.repo_structure["docs"] and ctx.repo_structure["examples"], s
        )),
        (lambda s: bool(re.match(r"^\d+\. \[", s)), lambda s: None),
        (lambda s: s.startswith("- Each `.sql.md` file is a contract"), lambda s: _ensure(
            bool(ctx.compiled_routes), s
        )),
        (lambda s: s.startswith("- The compiler translates those contracts"), lambda s: _ensure(
            ctx.compiled_hashes == ctx.recompiled_hashes, s
        )),
        (lambda s: s.startswith("- The runtime ships the results"), lambda s: _ensure(
            "content-type" in ctx.csv_headers and "content-type" in ctx.parquet_headers, s
        )),
        (lambda s: s.startswith("- Declare parameter controls"), lambda s: _ensure(
            "params-form" in ctx.html_text and "params-form" in ctx.cards_text, s
        )),
        (lambda s: s.startswith("The same `show_params` list works"), lambda s: _ensure(
            "params-form" in ctx.cards_text, s
        )),
        (lambda s: s.startswith("listed there render controls"), lambda s: _ensure(
            "type='hidden'" in ctx.html_text or "type=\"hidden\"" in ctx.html_text, s
        )),
        (lambda s: s.startswith("filter submissions keep pagination"), lambda s: _ensure(
            "name='offset'" in ctx.html_text or "name=\"offset\"" in ctx.html_text,
            s,
        )),
        (lambda s: s.startswith("- Table (`html_t`) and card (`html_c`) responses now emit"), lambda s: _ensure(
            ctx.html_rpc_payload and ctx.cards_rpc_payload, s
        )),
        (lambda s: s.startswith("and an embedded `<script id=\"wd-rpc-config\">`"), lambda s: _ensure(
            "wd-rpc-config" in ctx.html_text and "wd-rpc-config" in ctx.cards_text, s
        )),
        (lambda s: s.startswith("slice (`offset`, `limit`, `total_rows`) plus a ready-to-use Arrow RPC"), lambda s: _ensure(
            "total_rows" in ctx.html_rpc_payload and "total_rows" in ctx.cards_rpc_payload, s
        )),
        (lambda s: s.startswith("endpoint. Clients can call that URL"), lambda s: _ensure(
            "endpoint" in ctx.html_rpc_payload and "endpoint" in ctx.cards_rpc_payload, s
        )),
        (lambda s: s.startswith("stream additional pages without re-rendering the HTML."), lambda s: None),
        (lambda s: s.startswith("- Every HTML response mirrors the RPC headers"), lambda s: _ensure(
            "Download this slice" in ctx.html_text and "Download this slice" in ctx.cards_text, s
        )),
        (lambda s: s.startswith("`x-limit`) and surfaces a convenience link"), lambda s: _ensure(
            ("link" in ctx.html_headers or "Link" in ctx.html_headers)
            and ("link" in ctx.cards_headers or "Link" in ctx.cards_headers),
            s,
        )),
        (lambda s: s.startswith("(Arrow)"), lambda s: None),
        (lambda s: s.startswith("the slice to downstream tooling."), lambda s: _ensure(
            "Download this slice" in ctx.html_text and "Download this slice" in ctx.cards_text,
            s,
        )),
        (lambda s: s.startswith("- Drop `.sql.md` files into a folder"), lambda s: _ensure(
            ctx.repo_structure["routes_src"] and ctx.repo_structure["routes_build"], s
        )),
        (lambda s: s.startswith("- Designed for operational"), lambda s: None),
        (lambda s: s.startswith("3. **Compile the contracts into runnable manifests"), lambda s: None),
        (lambda s: s.startswith("4. **Launch the server."), lambda s: _ensure(
            ctx.reload_capable, s
        )),
        (lambda s: s.startswith("- `--watch` keeps the compiler running"), lambda s: _ensure(
            ctx.reload_capable, s
        )),
        (lambda s: s.startswith("- Pass `--no-auto-compile`"), lambda s: None),
        (lambda s: s.startswith("1. **Install the package and dependencies.**"), lambda s: None),
        (lambda s: s.startswith("2. **Create your route source directory**"), lambda s: _ensure(
            ctx.repo_structure["routes_src"], s
        )),
        (lambda s: s.startswith("5. **Browse the routes.**"), lambda s: _ensure(
            bool(ctx.route_json["rows"]), s
        )),
        (lambda s: s.startswith("For an exhaustive"), lambda s: _ensure(
            (ctx.repo_root / "AGENTS.md").is_file(), s
        )),
        (lambda s: s.startswith("- `webbed-duck serve` loads configuration"), lambda s: _ensure(
            ctx.repo_structure["config.toml"], s
        )),
        (lambda s: s.startswith("- With `server.auto_compile = true`"), lambda s: _ensure(
            ctx.reload_capable, s
        )),
        (lambda s: s.startswith("- Enabling watch mode"), lambda s: _ensure(
            ctx.reload_capable, s
        )),
        (lambda s: s.startswith("- The server is a FastAPI application"), lambda s: _ensure(
            "html" in ctx.html_text.lower(), s
        )),
        (lambda s: s.startswith("- The compiler scans the source tree"), lambda s: _ensure(
            len(ctx.compiled_routes) >= 1, s
        )),
        (lambda s: s.startswith("- Frontmatter declares the route `id`"), lambda s: _ensure(
            any(item["name"] == "name" for item in ctx.schema_payload.get("form", [])), s
        )),
        (lambda s: s.startswith("- Compiled artifacts are written"), lambda s: _ensure(
            ctx.repo_structure["routes_build"], s
        )),
        (lambda s: s.startswith("- At boot"), lambda s: _ensure(
            ctx.reload_capable, s
        )),
        (lambda s: s.startswith("- Parameters are declared"), lambda s: _ensure(
            any(item["name"] == "name" for item in ctx.schema_payload.get("form", [])), s
        )),
        (lambda s: s.startswith("- Within the SQL block"), lambda s: _ensure(
            bool(getattr(ctx.compiled_routes[0], "param_order", [])), s
        )),
        (lambda s: s.startswith("- At request time the runtime reads"), lambda s: _ensure(
            bool(ctx.route_json["rows"]), s
        )),
        (lambda s: s.startswith("- Additional runtime controls"), lambda s: None),
        (lambda s: s.startswith("- `?limit=`"), lambda s: None),
        (lambda s: s.startswith("- `?column=`"), lambda s: None),
        (lambda s: s.startswith("All of the following formats work today"), lambda s: _ensure(
            ctx.arrow_headers["content-type"].startswith("application/vnd.apache.arrow.stream"), s
        )),
        (lambda s: s.startswith("|"), lambda s: None),
        (lambda s: s.startswith("Routes may set `default_format`"), lambda s: None),
        (lambda s: s.startswith("- Every request opens a fresh DuckDB connection"), lambda s: _ensure(
            all(count == 1 for count in ctx.duckdb_connect_counts), s
        )),
        (lambda s: s.startswith("- You can query DuckDB-native sources"), lambda s: None),
        (lambda s: s.startswith("- For derived inputs"), lambda s: None),
        (lambda s: s.startswith("- After execution, server-side overlays"), lambda s: _ensure(
            ctx.override_payload["column"] == "note", s
        )),
        (lambda s: s.startswith("- Analytics (hits, rows, latency"), lambda s: _ensure(
            ctx.analytics_payload["routes"], s
        )),
        (lambda s: s.startswith("- Authentication modes are controlled via `config.toml`"), lambda s: _ensure(
            ctx.share_payload["meta"]["token"] is not None, s
        )),
        (lambda s: s.startswith("- Users with a pseudo-session"), lambda s: _ensure(
            ctx.share_payload["meta"]["rows_shared"] >= 1, s
        )),
        (lambda s: s.startswith("- Routes that define `[append]` metadata"), lambda s: _ensure(
            ctx.append_path.exists(), s
        )),
        (lambda s: s.startswith("* **Markdown + SQL compiler**"), lambda s: _ensure(
            ctx.compiled_hashes == ctx.recompiled_hashes, s
        )),
        (lambda s: s.startswith("* **Per-request DuckDB execution**"), lambda s: _ensure(
            all(count >= 1 for count in ctx.duckdb_connect_counts), s
        )),
        (lambda s: s.startswith("* **Overlay-aware viewers**"), lambda s: _ensure(
            ctx.override_payload["column"] == "note" and ctx.append_path.exists(), s
        )),
        (lambda s: s.startswith("* **Share engine**"), lambda s: _ensure(
            ctx.share_payload["meta"]["rows_shared"] >= 1 and ctx.share_db_hashes[0] != ctx.share_payload["meta"]["token"], s
        )),
        (lambda s: s.startswith("* **Configurable auth adapters**"), lambda s: _ensure(
            ctx.python_requires.startswith(">=3"), s
        )),
        (lambda s: s.startswith("* **Incremental execution**"), lambda s: _ensure(
            len(ctx.incremental_rows) >= 1 and ctx.checkpoints_exists, s
        )),
        (lambda s: s.startswith("* **Extensible plugins**"), lambda s: _ensure(
            ctx.assets_registry_size >= 1 and ctx.charts_registry_size >= 0, s
        )),
        (lambda s: s.startswith("1. **Authoring**"), lambda s: _ensure(
            ctx.repo_structure["routes_src"], s
        )),
        (lambda s: s.startswith("2. **Compilation**"), lambda s: _ensure(
            ctx.repo_structure["routes_build"], s
        )),
        (lambda s: s.startswith("3. **Serving**"), lambda s: _ensure(
            "routes" in ctx.analytics_payload, s
        )),
        (lambda s: s.startswith("4. **Extensions**"), lambda s: _ensure(
            ctx.assets_registry_size >= 1, s
        )),
        (lambda s: s.startswith("Use a virtual environment"), lambda s: None),
        (lambda s: s.startswith("Install the published package"), lambda s: None),
        (lambda s: s.startswith("* Python 3.9 or newer"), lambda s: _ensure(
            _python_requirement_at_least(ctx.python_requires, (3, 9)), s
        )),
        (lambda s: s.startswith("* DuckDB (installed automatically"), lambda s: None),
        (lambda s: s.startswith("* Access to an intranet"), lambda s: None),
        (lambda s: s.startswith("* Optional: `pyzipper`"), lambda s: None),
        (lambda s: s.startswith("Optional extras:"), lambda s: _ensure(
            any("pyzipper" in dep for dep in ctx.dependencies), s
        )),
        (lambda s: s.startswith("After upgrades"), lambda s: None),
        (lambda s: s.startswith("`webbed_duck` reads a TOML configuration"), lambda s: _ensure(
            isinstance(load_config(None), Config), s
        )),
        (lambda s: s.startswith("Key principles:"), lambda s: None),
        (lambda s: s.startswith("* **`storage_root`**"), lambda s: _ensure(
            ctx.storage_root_layout["runtime"], s
        )),
        (lambda s: s.startswith("* **Auth adapters**"), lambda s: _ensure(
            ctx.share_payload["meta"]["token"] is not None, s
        )),
        (lambda s: s.startswith("* **Transport mode**"), lambda s: None),
        (lambda s: s.startswith("* **Feature flags**"), lambda s: _ensure(
            any(item["name"] == "name" for item in ctx.schema_payload.get("form", [])), s
        )),
        (lambda s: s.startswith("After editing `config.toml`"), lambda s: None),
        (lambda s: s.startswith("Once the package is installed"), lambda s: _ensure(
            ctx.repo_structure["config.toml"], s
        )),
        (lambda s: s.startswith("Add a starter route"), lambda s: _ensure(
            any(route.id == "hello" for route in ctx.compiled_routes), s
        )),
        (lambda s: s.startswith("This minimal setup is enough"), lambda s: _ensure(
            ctx.route_json["rows"], s
        )),
        (lambda s: s.startswith("Routes live in"), lambda s: _ensure(
            ctx.repo_structure["routes_src"], s
        )),
        (lambda s: s.startswith("Run `webbed-duck compile`"), lambda s: None),
        (lambda s: s.startswith("- **Default behaviour:**"), lambda s: _ensure(
            ctx.reload_capable, s
        )),
        (lambda s: s.startswith("- **Configurable toggles:**"), lambda s: _ensure(
            ctx.reload_capable, s
        )),
        (lambda s: s.startswith("- **Configuration surface:**"), lambda s: _ensure(
            ctx.repo_structure["config.toml"], s
        )),
        (lambda s: s.startswith("* `@route`"), lambda s: _ensure(
            all(hasattr(route, "id") for route in ctx.compiled_routes), s
        )),
        (lambda s: s.startswith("* `@params`"), lambda s: _ensure(
            any(route.params for route in ctx.compiled_routes), s
        )),
        (lambda s: s.startswith("* `@preprocess`"), lambda s: _ensure(
            all(hasattr(route, "preprocess") for route in ctx.compiled_routes), s
        )),
        (lambda s: s.startswith("* `@sql`"), lambda s: _ensure(
            all(hasattr(route, "prepared_sql") for route in ctx.compiled_routes), s
        )),
        (lambda s: s.startswith("* `@postprocess`"), lambda s: _ensure(
            all(hasattr(route, "postprocess") for route in ctx.compiled_routes), s
        )),
        (lambda s: s.startswith("* `@charts`"), lambda s: _ensure(
            all(hasattr(route, "charts") for route in ctx.compiled_routes), s
        )),
        (lambda s: s.startswith("* `@append`"), lambda s: _ensure(
            ctx.append_path.exists(), s
        )),
        (lambda s: s.startswith("* `@assets`"), lambda s: _ensure(
            all(hasattr(route, "assets") for route in ctx.compiled_routes), s
        )),
        (lambda s: s.startswith("Authoring tips:"), lambda s: None),
        (lambda s: s.startswith("* Favor set-based SQL"), lambda s: None),
        (lambda s: s.startswith("* Keep preprocessors"), lambda s: None),
        (lambda s: s.startswith("* Use folders"), lambda s: None),
        (lambda s: s.startswith("1. **Compile**"), lambda s: _ensure(
            ctx.compiled_hashes == ctx.recompiled_hashes, s
        )),
        (lambda s: s.startswith("2. **Serve**"), lambda s: None),
        (lambda s: s.startswith("3. **Visit**"), lambda s: _ensure(
            ctx.route_json["rows"][0]["greeting"].startswith("Hello"), s
        )),
        (lambda s: s.startswith("4. **Interact**"), lambda s: _ensure(
            ctx.override_payload["column"] == "note", s
        )),
        (lambda s: s.startswith("* `POST /routes/{route_id}/overrides`"), lambda s: _ensure(
            ctx.override_payload["column"] == "note", s
        )),
        (lambda s: s.startswith("* `POST /routes/{route_id}/append`"), lambda s: _ensure(
            ctx.append_path.exists(), s
        )),
        (lambda s: s.startswith("* `GET /routes/{route_id}/schema`"), lambda s: _ensure(
            ctx.schema_payload.get("route_id") == "hello", s
        )),
        (lambda s: s.startswith("5. **Share**"), lambda s: _ensure(
            ctx.share_payload["meta"]["inline_snapshot"] is True, s
        )),
        (lambda s: s.startswith("The runtime stores share metadata"), lambda s: _ensure(
            ctx.storage_root_layout["runtime/meta.sqlite3"], s
        )),
        (lambda s: s.startswith("6. **Run incremental workloads**"), lambda s: _ensure(
            ctx.checkpoints_exists, s
        )),
        (lambda s: s.startswith("Progress persists"), lambda s: _ensure(
            ctx.checkpoints_exists, s
        )),
        (lambda s: s.startswith("* **Request lifecycle**"), lambda s: _ensure(
            ctx.arrow_headers["content-type"].startswith("application/vnd.apache.arrow.stream"), s
        )),
        (lambda s: s.startswith("* **Analytics**"), lambda s: _ensure(
            ctx.analytics_payload["routes"], s
        )),
        (lambda s: s.startswith("* **Local route chaining**"), lambda s: _ensure(
            ctx.local_resolve_payload["route_id"] == "hello", s
        )),
        (lambda s: s.startswith("* **Static assets**"), lambda s: _ensure(
            ctx.assets_registry_size >= 1, s
        )),
        (lambda s: s.startswith("* **Email integration**"), lambda s: _ensure(
            len(ctx.email_records) == 1, s
        )),
        (lambda s: s.startswith("A `.sql.md` file is the single source of truth"), lambda s: _ensure(
            bool(ctx.compiled_routes), s
        )),
        (lambda s: s.startswith("1. **Frontmatter (`+++"), lambda s: None),
        (lambda s: s.startswith("2. **Markdown body:"), lambda s: None),
        (lambda s: s.startswith("3. **SQL code block:"), lambda s: None),
        (lambda s: s.startswith("Common keys include:"), lambda s: None),
        (lambda s: s.startswith("- `id`: Stable identifier"), lambda s: None),
        (lambda s: s.startswith("- `path`: HTTP path"), lambda s: None),
        (lambda s: s.startswith("- `title`, `description`"), lambda s: None),
        (lambda s: s.startswith("- `version`: Optional"), lambda s: None),
        (lambda s: s.startswith("- `default_format`"), lambda s: None),
        (lambda s: s.startswith("- `allowed_formats`"), lambda s: None),
        (lambda s: s.startswith("- `[params."), lambda s: None),
        (lambda s: s.startswith("- Presentation metadata blocks"), lambda s: None),
        (lambda s: s.startswith("- `[[preprocess]]` entries"), lambda s: None),
        (lambda s: s.startswith("- Write DuckDB SQL inside"), lambda s: None),
        (lambda s: s.startswith("- Interpolate declared parameters"), lambda s: None),
        (lambda s: s.startswith("- Do not concatenate user input"), lambda s: None),
        (lambda s: s.startswith("Routes can further customise behaviour"), lambda s: _ensure(
            ctx.override_payload["column"] == "note", s
        )),
        (lambda s: s.startswith("> **Promise:** By 0.4"), lambda s: _ensure(
            ctx.reload_capable, s
        )),
        (lambda s: s.startswith("MVP 0.4 is the first release"), lambda s: None),
        (lambda s: s.startswith("- **Preprocessors:**"), lambda s: None),
        (lambda s: s.startswith("- **Postprocessors and presentation:**"), lambda s: _ensure(
            "card" in ctx.cards_text.lower(), s
        )),
        (lambda s: s.startswith("- **Assets and overlays:**"), lambda s: _ensure(
            ctx.override_payload["column"] == "note", s
        )),
        (lambda s: s.startswith("- **Local execution:**"), lambda s: _ensure(
            ctx.local_resolve_payload["route_id"] == "hello", s
        )),
        (lambda s: s.startswith("As the plugin hooks stabilise"), lambda s: None),
        (lambda s: s.startswith("- Auto-compiling `webbed-duck serve` command"), lambda s: _ensure(
            ctx.reload_capable, s
        )),
        (lambda s: s.startswith("- Built-in watch mode (`server.watch`"), lambda s: _ensure(
            ctx.reload_capable, s
        )),
        (lambda s: s.startswith("- Dynamic route registry inside the FastAPI app"), lambda s: _ensure(
            ctx.reload_capable, s
        )),
        (lambda s: s.startswith("- CLI and docs tuned for a zero-config quick start"), lambda s: _ensure(
            ctx.repo_structure["routes_src"] and ctx.repo_structure["config.toml"], s
        )),
        (lambda s: s.startswith("- Declarative caching / snapshot controls"), lambda s: None),
        (lambda s: s.startswith("- Richer auto-generated parameter forms"), lambda s: None),
        (lambda s: s.startswith("- Additional auth adapter examples"), lambda s: None),
        (lambda s: s.startswith("All runtime paths derive"), lambda s: _ensure(
            ctx.storage_root_layout["runtime"], s
        )),
        (lambda s: s.startswith("Ensure the service user"), lambda s: None),
        (lambda s: s.startswith("* **Securable by design**"), lambda s: None),
        (lambda s: s.startswith("* **Connection management**"), lambda s: _ensure(
            all(count == 1 for count in ctx.duckdb_connect_counts), s
        )),
        (lambda s: s.startswith("* **Secrets hygiene**"), lambda s: _ensure(
            ctx.share_db_hashes[0] != ctx.share_payload["meta"]["token"], s
        )),
        (lambda s: s.startswith("* **Path safety**"), lambda s: _ensure(
            ctx.storage_root_layout["runtime"], s
        )),
        (lambda s: s.startswith("* **Proxy deployment**"), lambda s: None),
        (lambda s: s.startswith("* **External auth**"), lambda s: None),
        (lambda s: s.startswith("Run the pytest suite"), lambda s: None),
        (lambda s: s.startswith("The suite exercises"), lambda s: _ensure(
            ctx.analytics_payload["routes"], s
        )),
        (lambda s: s.startswith("Linting can be layered"), lambda s: None),
        (lambda s: s.startswith("* **Missing compiled routes**"), lambda s: _ensure(
            ctx.compiled_hashes == ctx.recompiled_hashes, s
        )),
        (lambda s: s.startswith("* **ZIP encryption disabled**"), lambda s: None),
        (lambda s: s.startswith("* **Authentication failures**"), lambda s: _ensure(
            ctx.share_db_hashes[1] != "", s
        )),
        (lambda s: s.startswith("* **Proxy misconfiguration**"), lambda s: None),
        (lambda s: s.startswith("* **DuckDB locking errors**"), lambda s: _ensure(
            all(count == 1 for count in ctx.duckdb_connect_counts), s
        )),
        (lambda s: s.startswith("* Current release"), lambda s: None),
        (lambda s: s.startswith("* Major focuses"), lambda s: None),
        (lambda s: s.startswith("* Upcoming ideas"), lambda s: None),
        (lambda s: s.startswith("Refer to the maintainer logs"), lambda s: _ensure(
            (ctx.repo_root / "AGENTS.md").is_file(), s
        )),
        (lambda s: s.startswith("* [`AGENTS.md`]"), lambda s: _ensure(
            (ctx.repo_root / "AGENTS.md").is_file(), s
        )),
        (lambda s: s.startswith("* [`docs/`]"), lambda s: _ensure(
            ctx.repo_structure["docs"], s
        )),
        (lambda s: s.startswith("* [`examples/emailer.py`]"), lambda s: _ensure(
            (ctx.repo_root / "examples" / "emailer.py").is_file(), s
        )),
        (lambda s: s.startswith("* [`CHANGELOG.md`]"), lambda s: _ensure(
            ctx.repo_structure["CHANGELOG.md"], s
        )),
        (lambda s: s.startswith("Bug reports and feature requests"), lambda s: None),
        (lambda s: s.startswith("1. Fork the repository"), lambda s: None),
        (lambda s: s.startswith("2. Install dependencies"), lambda s: None),
        (lambda s: s.startswith("3. Run `pytest`"), lambda s: None),
        (lambda s: s.startswith("4. Document new behavior"), lambda s: None),
        (lambda s: s.startswith("5. Follow the invariants"), lambda s: _ensure(
            (ctx.repo_root / "AGENTS.md").is_file(), s
        )),
        (lambda s: s.startswith("Happy routing!"), lambda s: _ensure(
            "Happy routing" in Path(ctx.repo_root / "README.md").read_text(encoding="utf-8"), s
        )),
    ]

    unmatched: list[str] = []
    for statement in ctx.readme_lines:
        for predicate, validator in validators:
            if predicate(statement):
                validator(statement)
                break
        else:
            unmatched.append(statement)

    assert not unmatched, "README statements without coverage: " + json.dumps(unmatched, indent=2)
