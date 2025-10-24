from pydantic import SecretStr
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from chift_mcp.constants import DEFAULT_CONFIG


class Chift(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="CHIFT_", extra="ignore"
    )
    client_secret: SecretStr
    client_id: str
    account_id: str
    url_base: str = "https://api.chift.eu"
    consumer_id: str | None = None
    function_config: dict[str, list[str]] = DEFAULT_CONFIG
    server_name: str = "Chift MCP Server"
    proxy_url: str = "https://docs.chift.eu/mcp"
    marketplace_id: str | None = None
