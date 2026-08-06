from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    debug: bool = True
    app_env: str = "development"

    # App URLs used by Microsoft SSO redirect flows.
    # Override in .env / environment when deployed (must match the
    # redirect URIs registered in your Entra ID app registration).
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
