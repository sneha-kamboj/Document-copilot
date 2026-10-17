from pathlib import Path

from cryptography.hazmat.backends.openssl import backend
from pydantic import computed_field
from pydantic_settings import BaseSettings,SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file= BACKEND_DIR/".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str
    database_url: str


    openai_api_key: str
    openai_chat_model:str="gpt-4.1"
    openapi_embeddings_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536


    allowed_origins:str = "http://localhost:5173"
    enable_docs:bool=True

    retrieval_candidates:int =30
    retrieval_top_k:int = 8
    retrieval_rrf_k:int =60
    retrieval_neighbor_radius:int=1


    @computed_field()
    @property


    def cors_origin(self)->list[str]:
        return[
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]

settings = Settings()