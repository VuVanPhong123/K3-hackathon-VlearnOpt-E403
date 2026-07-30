from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VLearn Tutor API"
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    storage_dir: Path = Path("app/storage/documents")
    metadata_dir: Path = Path("app/storage/metadata")
    database_path: Path = Path("app/storage/index/vlearn.db")
    embedding_cache_dir: Path = Path("app/storage/model-cache")
    page_cache_dir: Path = Path("app/storage/page-cache")
    max_upload_mb: int = 50
    primary_provider: str = "openai"
    enable_gemini_fallback: bool = True
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    openai_timeout_seconds: float = 45
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_timeout_seconds: float = 45
    embedding_provider: str = "huggingface"
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 16
    embedding_timeout_seconds: float = 120
    enable_reranker: bool = False
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_top_n: int = 12
    reranker_final_n: int = 6
    retrieval_lexical_top_k: int = 20
    retrieval_dense_top_k: int = 20
    retrieval_fused_top_k: int = 12
    retrieval_final_top_k: int = 6
    retrieval_min_score: float = 0.2
    chat_recent_message_limit: int = 12
    chat_summary_trigger_messages: int = 16
    chat_max_history_chars: int = 24000
    chat_summary_max_chars: int = 4000
    max_evidence_chars: int = 24000
    max_query_chars: int = 2000
    max_selected_text_chars: int = 6000
    max_selection_chars: int = 6000
    primary_text_provider: str = "openai"
    fallback_text_provider: str = "gemini"
    router_provider: str = "gemini"
    router_model: str = ""
    router_confidence_threshold: float = 0.72
    vision_primary_provider: str = "gemini"
    vision_fallback_provider: str = "openai"
    gemini_vision_model: str = ""
    openai_vision_model: str = ""
    page_render_scale: float = 1.6
    region_render_scale: float = 2.0
    max_visual_image_bytes: int = 10_000_000
    text_selection_match_threshold: int = 78
    verifier_enabled: bool = True
    verifier_provider: str = "openai"
    verifier_model: str = ""
    enable_debug_endpoints: bool = True
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
