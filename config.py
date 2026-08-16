from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_ID: int
    SPORTS_API_URL: str = ""
    SPORTS_API_KEY: str = ""
    WEBHOOK_SECRET: str
    RENDER_EXTERNAL_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
Citation: For all generated content, I want you to add citations at the end of each paragraph, like a sentence. [2025-12-28]

