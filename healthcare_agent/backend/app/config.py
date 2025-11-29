"""Configuration settings for the application."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    mongo_uri: str = "mongodb://localhost:27017/agentic_volunteer"
    database_name: str = "agentic_volunteer"
    
    # JWT Authentication settings
    jwt_secret_key: str = ""  # REQUIRED: Set via JWT_SECRET_KEY env var
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Twilio SMS settings (optional)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    
    # Twilio WhatsApp settings (optional)
    twilio_whatsapp_from: str = "whatsapp:+14155238886"  # Default Twilio WhatsApp sandbox number
    twilio_content_sid: str = ""  # Content template SID for WhatsApp messages (optional)
    
    # NotificationAPI settings (optional - alternative to Twilio)
    notificationapi_client_id: str = ""
    notificationapi_client_secret: str = ""
    
    # Redis/Celery settings
    redis_url: str = "redis://localhost:6379/0"
    
    # LLM Settings for Intelligent Volunteer Queueing
    openai_api_key: str = ""  # OpenAI API key for GPT models
    anthropic_api_key: str = ""  # Anthropic API key for Claude (optional)
    llm_provider: str = "openai"  # "openai" or "anthropic"
    llm_model: str = "gpt-3.5-turbo"  # Model to use (gpt-3.5-turbo, gpt-4, etc.)
    enable_llm_queueing: bool = True  # Enable/disable LLM-powered volunteer queueing
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        """Validate required settings on initialization."""
        super().__init__(**kwargs)
        # Validate critical production settings
        if not self.jwt_secret_key:
            import os
            if os.getenv("JWT_SECRET_KEY"):
                self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
            else:
                # For development, use a default but warn
                # In production, this should be set via environment variable
                import warnings
                self.jwt_secret_key = "dev-secret-key-change-in-production"
                warnings.warn(
                    "JWT_SECRET_KEY not set. Using default dev key. "
                    "Set JWT_SECRET_KEY in .env file for production!",
                    UserWarning
                )


settings = Settings()

