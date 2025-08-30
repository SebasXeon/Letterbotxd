from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    log_level: int = 10
    gemini_api_key: str = ""
    page_access_token: str = ""