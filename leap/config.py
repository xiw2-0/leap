import pydantic
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Leap - Web Trading APIs for China A-Share"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    QMT_DATA_PATH: str = ""
    QMT_ACCOUNT: str = ""
    QMT_ACCOUNT_TYPE: str = pydantic.Field(default="STOCK", examples=["STOCK", "CREDIT"])
    QMT_EXPORT_PATH: str = pydantic.Field(default=".", description="QMT导出数据的路径")


settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump())
