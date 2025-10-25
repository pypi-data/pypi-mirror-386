"""Configuration loading for webbed_duck."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for older interpreters
    import tomli as tomllib  # type: ignore


@dataclass(slots=True)
class ServerConfig:
    """HTTP server configuration."""

    storage_root: Path = Path("storage")
    theme: str = "system"
    host: str = "127.0.0.1"
    port: int = 8000
    source_dir: Path | None = Path("routes_src")
    build_dir: Path = Path("routes_build")
    auto_compile: bool = True
    watch: bool = False
    watch_interval: float = 1.0


@dataclass(slots=True)
class UIConfig:
    """User interface toggles exposed to postprocessors."""

    show_http_warning: bool = True
    error_taxonomy_banner: bool = True


@dataclass(slots=True)
class AnalyticsConfig:
    """Runtime analytics collection controls."""

    enabled: bool = True
    weight_interactions: int = 1


@dataclass(slots=True)
class AuthConfig:
    """Authentication adapter selection and tunables."""

    mode: str = "none"
    external_adapter: str | None = None
    allowed_domains: Sequence[str] = field(default_factory=list)
    session_ttl_minutes: int = 45
    remember_me_days: int = 7


@dataclass(slots=True)
class EmailConfig:
    """Outbound email adapter configuration."""

    adapter: str | None = None
    from_address: str = "no-reply@company.local"
    share_token_ttl_minutes: int = 90
    bind_share_to_user_agent: bool = False
    bind_share_to_ip_prefix: bool = False


@dataclass(slots=True)
class ShareConfig:
    """Share workflow configuration."""

    max_total_size_mb: int = 15
    zip_attachments: bool = True
    zip_passphrase_required: bool = False
    watermark: bool = True


@dataclass(slots=True)
class Config:
    """Top-level configuration container."""

    server: ServerConfig = field(default_factory=ServerConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    share: ShareConfig = field(default_factory=ShareConfig)


def _as_path(value: Any) -> Path:
    if isinstance(value, Path):
        return value
    return Path(str(value))


def _load_toml(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def load_config(path: str | Path | None = None) -> Config:
    """Load configuration from ``path`` if provided, otherwise defaults.

    Parameters
    ----------
    path:
        Path to a ``config.toml`` file. When ``None`` the default configuration
        (with no file) is used.
    """

    cfg = Config()
    if path is None:
        return cfg

    data = _load_toml(Path(path))
    server_data = data.get("server")
    if isinstance(server_data, Mapping):
        cfg.server = _parse_server(server_data, base=cfg.server)
    ui_data = data.get("ui")
    if isinstance(ui_data, Mapping):
        cfg.ui = _parse_ui(ui_data, base=cfg.ui)
    analytics_data = data.get("analytics")
    if isinstance(analytics_data, Mapping):
        cfg.analytics = _parse_analytics(analytics_data, base=cfg.analytics)
    auth_data = data.get("auth")
    if isinstance(auth_data, Mapping):
        cfg.auth = _parse_auth(auth_data, base=cfg.auth)
    email_data = data.get("email")
    if isinstance(email_data, Mapping):
        cfg.email = _parse_email(email_data, base=cfg.email)
    share_data = data.get("share")
    if isinstance(share_data, Mapping):
        cfg.share = _parse_share(share_data, base=cfg.share)
    return cfg


def _parse_server(data: Mapping[str, Any], base: ServerConfig) -> ServerConfig:
    overrides: MutableMapping[str, Any] = {}
    if "storage_root" in data:
        overrides["storage_root"] = _as_path(data["storage_root"])
    if "theme" in data:
        overrides["theme"] = str(data["theme"])
    if "host" in data:
        overrides["host"] = str(data["host"])
    if "port" in data:
        overrides["port"] = int(data["port"])
    if "source_dir" in data:
        overrides["source_dir"] = (
            None if data["source_dir"] is None else _as_path(data["source_dir"])
        )
    if "build_dir" in data:
        overrides["build_dir"] = _as_path(data["build_dir"])
    if "auto_compile" in data:
        overrides["auto_compile"] = bool(data["auto_compile"])
    if "watch" in data:
        overrides["watch"] = bool(data["watch"])
    if "watch_interval" in data:
        overrides["watch_interval"] = float(data["watch_interval"])
    if not overrides:
        return base
    return replace(base, **overrides)


def _parse_ui(data: Mapping[str, Any], base: UIConfig) -> UIConfig:
    overrides: MutableMapping[str, Any] = {}
    if "show_http_warning" in data:
        overrides["show_http_warning"] = bool(data["show_http_warning"])
    if "error_taxonomy_banner" in data:
        overrides["error_taxonomy_banner"] = bool(data["error_taxonomy_banner"])
    if not overrides:
        return base
    return replace(base, **overrides)


def _parse_analytics(data: Mapping[str, Any], base: AnalyticsConfig) -> AnalyticsConfig:
    overrides: MutableMapping[str, Any] = {}
    if "enabled" in data:
        overrides["enabled"] = bool(data["enabled"])
    if "weight_interactions" in data:
        overrides["weight_interactions"] = int(data["weight_interactions"])
    if not overrides:
        return base
    return replace(base, **overrides)


def _parse_auth(data: Mapping[str, Any], base: AuthConfig) -> AuthConfig:
    overrides: MutableMapping[str, Any] = {}
    if "mode" in data:
        overrides["mode"] = str(data["mode"])
    if "external_adapter" in data:
        overrides["external_adapter"] = str(data["external_adapter"]) if data["external_adapter"] is not None else None
    if "allowed_domains" in data and isinstance(data["allowed_domains"], Sequence):
        overrides["allowed_domains"] = [str(item) for item in data["allowed_domains"]]
    if "session_ttl_minutes" in data:
        overrides["session_ttl_minutes"] = int(data["session_ttl_minutes"])
    if "remember_me_days" in data:
        overrides["remember_me_days"] = int(data["remember_me_days"])
    if not overrides:
        return base
    return replace(base, **overrides)


def _parse_email(data: Mapping[str, Any], base: EmailConfig) -> EmailConfig:
    overrides: MutableMapping[str, Any] = {}
    if "adapter" in data:
        overrides["adapter"] = str(data["adapter"]) if data["adapter"] is not None else None
    if "from_address" in data:
        overrides["from_address"] = str(data["from_address"])
    if "share_token_ttl_minutes" in data:
        overrides["share_token_ttl_minutes"] = int(data["share_token_ttl_minutes"])
    if "bind_share_to_user_agent" in data:
        overrides["bind_share_to_user_agent"] = bool(data["bind_share_to_user_agent"])
    if "bind_share_to_ip_prefix" in data:
        overrides["bind_share_to_ip_prefix"] = bool(data["bind_share_to_ip_prefix"])
    if not overrides:
        return base
    return replace(base, **overrides)


def _parse_share(data: Mapping[str, Any], base: ShareConfig) -> ShareConfig:
    overrides: MutableMapping[str, Any] = {}
    if "max_total_size_mb" in data:
        overrides["max_total_size_mb"] = int(data["max_total_size_mb"])
    if "zip_attachments" in data:
        overrides["zip_attachments"] = bool(data["zip_attachments"])
    if "zip_passphrase_required" in data:
        overrides["zip_passphrase_required"] = bool(data["zip_passphrase_required"])
    if "watermark" in data:
        overrides["watermark"] = bool(data["watermark"])
    if not overrides:
        return base
    return replace(base, **overrides)


__all__ = [
    "AnalyticsConfig",
    "Config",
    "ServerConfig",
    "UIConfig",
    "AuthConfig",
    "EmailConfig",
    "ShareConfig",
    "load_config",
]
