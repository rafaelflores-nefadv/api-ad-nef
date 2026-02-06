from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="dev", validation_alias="APP_ENV")
    cors_allow_origins: List[str] = Field(default=["*"], validation_alias="CORS_ALLOW_ORIGINS")

    jwt_secret_key: str = Field(default="change-me", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_minutes: int = Field(default=30, validation_alias="JWT_ACCESS_TOKEN_MINUTES")

    samba_tool_path: str = Field(default="samba-tool", validation_alias="SAMBA_TOOL_PATH")
    samba_realm: str | None = Field(default=None, validation_alias="SAMBA_REALM")
    samba_workgroup: str | None = Field(default=None, validation_alias="SAMBA_WORKGROUP")
    samba_auth_user: str | None = Field(default=None, validation_alias="SAMBA_AUTH_USER")
    samba_auth_domain: str | None = Field(default=None, validation_alias="SAMBA_AUTH_DOMAIN")
    samba_timeout_seconds: int = Field(default=20, validation_alias="SAMBA_TIMEOUT_SECONDS")
    samba_dry_run: bool = Field(default=False, validation_alias="SAMBA_DRY_RUN")

    db_url: str = Field(default="sqlite:///./app.db", validation_alias="DATABASE_URL")

    rate_limit_per_minute: int = Field(default=60, validation_alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, validation_alias="RATE_LIMIT_BURST")

    ldap_uri: str = Field(default="ldap://SRV-ADMASTER.nabarrete.local", validation_alias="LDAP_URI")
    bind_dn: str = Field(
        default="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local",
        validation_alias="BIND_DN",
    )
    bind_pw: str = Field(default="Nabarrete@2026", validation_alias="BIND_PW")
    base_dn: str = Field(default="OU=Nabarrete,DC=nabarrete,DC=local", validation_alias="BASE_DN")
    users_ou: str = Field(default="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local", validation_alias="USERS_OU")
    domain: str = Field(default="nabarrete.local", validation_alias="DOMAIN")


settings = Settings()
