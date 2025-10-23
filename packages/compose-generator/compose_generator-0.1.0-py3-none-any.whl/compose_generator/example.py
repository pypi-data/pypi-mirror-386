# Example
from compose_generator import Generator

TEMPLATE = """version: "3.9"

networks:
  common-net:
    external: true

x-serv-common-env: &serv-common-env
  [ENV]

services:
  api:
    image: /project/user/super-project/api:[VERSION]
    networks:
      - common-net
    ports:
      - ${APP_SERVER_PORT}:${APP_SERVER_PORT}
    environment:
      <<: *serv-common-env
    restart:
      unless-stopped
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FromEnvFile(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(Path(__file__).resolve().parent, "example.env"),
        extra="ignore",
    )


class BaseConnection(FromEnvFile):
    USER: str
    PASS: str
    HOST: str
    PORT: int
    NAME: str

    def get_connection_config(self) -> dict:
        return {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": self.HOST,
                "port": self.PORT,
                "user": self.USER,
                "password": self.PASS,
                "database": self.NAME,
            },
        }


class DefaultDB(BaseConnection):
    model_config = SettingsConfigDict(env_prefix="DEFAULT_DB_")


class App(FromEnvFile):
    model_config = SettingsConfigDict(env_prefix="APP_")
    SERVER_PORT: int
    VERSION: str = '1.0.0'


class API(FromEnvFile):
    model_config = SettingsConfigDict(env_prefix="API_")
    KEY: str


class Swagger(FromEnvFile):
    model_config = SettingsConfigDict(env_prefix="SWAGGER_")
    LOGIN: str
    PASSWORD: str


class JWT(FromEnvFile):
    model_config = SettingsConfigDict(env_prefix="JWT_")
    SECRET_KEY: str
    EXPIRES_SECONDS: int


class Settings(BaseSettings):
    app: App = Field(default_factory=App)
    db: DefaultDB = Field(default_factory=DefaultDB)
    jwt: JWT = Field(default_factory=JWT)
    api: API = Field(default_factory=API)
    swagger: Swagger = Field(default_factory=Swagger)


if __name__ == "__main__":
    stt = Settings()
    generator = Generator(
        settings=stt,
        template=TEMPLATE,
        version=stt.app.VERSION,
    )
    generator.generate()
