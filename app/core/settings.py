from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    debug: bool = True
    app_env: str = "development"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
