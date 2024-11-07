import os

from pydantic_settings import BaseSettings, SettingsConfigDict


_env_file_path = os.path.join(os.path.dirname(__file__), ".env")


class Configuration(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_file_path, extra="ignore")

    cors_allow_credentials     : bool       = True
    cors_allow_headers         : tuple[str] = ("*",)
    cors_allow_methods         : tuple[str] = ("*",)
    cors_allow_origins         : tuple[str] = ("http://localhost:8080",)
    database_url               : str
    sentry_dsn                 : str
    sentry_traces_sample_rate  : float      = 1.0
    sentry_profiles_sample_rate: float      = 1.0


configuration = Configuration()