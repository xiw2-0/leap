import pydantic_settings

class Settings(pydantic_settings.BaseSettings):
    PROJECT_NAME: str = "Leap - Web Trading APIs for China A-Share"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

settings = Settings()