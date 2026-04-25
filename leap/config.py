import pydantic
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Leap - Web Trading APIs for China A-Share"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    QMT_DATA_PATH: str = ""
    QMT_ACCOUNT: str = ""
    QMT_ACCOUNT_TYPE: str = pydantic.Field(
        default="STOCK", examples=["STOCK", "CREDIT"])
    QMT_EXPORT_PATH: str = pydantic.Field(
        default=".", description="QMT 导出数据的路径")

    LOG_LEVEL: str = pydantic.Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    LOG_DIR: str = pydantic.Field(
        default="logs", description="Directory for log files")

    QUOTE_GUARD_WORK_SLEEP: float = pydantic.Field(
        default=1.8, description="Seconds to sleep between quote guard checks during working hours")
    QUOTE_GUARD_LATENCY_THRESHOLD: float = pydantic.Field(
        default=1.8, description="Seconds beyond which quote data is considered stale")


settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump())
