from pydantic import computed_field
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str
    database_url: str


    openai_api_key: str
    openapi_embeddings_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536


    allowed_origins:str = "http://localhost:5173"

    @computed_field
    @property

    def cors_origin(self)->list[str]:
        return[
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]