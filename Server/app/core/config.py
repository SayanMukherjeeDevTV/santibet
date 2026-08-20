"""Central application settings, loaded from environment variables / .env."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="dev")  # dev | staging | prod
    log_level: str = Field(default="INFO")

    # Database
    database_url: str = Field(default="postgresql+asyncpg://santibet_app:changeme@localhost:5432/santibet_dev")
    database_url_test: str = Field(default="postgresql+asyncpg://santibet_app:changeme@localhost:5432/santibet_test")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Auth
    jwt_secret: str = Field(default="change_this_to_a_long_random_string")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=30)

    # CORS
    cors_origins: str = Field(default="http://localhost:3000")

    # Feature flags
    platform_real_money_enabled: bool = Field(default=False)

    # Trading defaults
    default_amm_liquidity_param: float = Field(default=100.0)
    taker_fee_bps: int = Field(default=100)  # basis points

    # OpenAI
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")
    openai_base_url: str = Field(default="")

    # Stripe
    stripe_secret_key: str = Field(default="")
    stripe_webhook_secret: str = Field(default="")
    stripe_publishable_key: str = Field(default="")

    # External signal providers
    newsapi_key: str = Field(default="")
    fred_api_key: str = Field(default="")

    # Geofencing
    geofence_blocked_regions: str = Field(default="")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def geofence_blocked_regions_list(self) -> list[str]:
        return [r.strip() for r in self.geofence_blocked_regions.split(",") if r.strip()]

    @property
    def is_prod(self) -> bool:
        return self.environment == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
