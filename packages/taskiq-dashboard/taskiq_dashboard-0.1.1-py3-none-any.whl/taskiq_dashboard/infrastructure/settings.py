import os
from typing import Any
from urllib.parse import quote, urlparse

import pydantic_settings
from pydantic import BaseModel, SecretStr, model_validator


class PostgresSettings(BaseModel):
    """Настройки для подключения к PostgreSQL."""

    driver: str = 'postgresql+asyncpg'
    host: str = 'postgres'
    port: int = 5432
    user: str = 'taskiq-dashboard'
    password: SecretStr = SecretStr('look_in_vault')
    database: str = 'taskiq-dashboard'

    min_pool_size: int = 1
    max_pool_size: int = 5

    @property
    def dsn(self) -> SecretStr:
        """
        Возвращает строку подключения к PostgreSQL составленную из параметров класса.

        Пример использования с asyncpg:

            >>> import asyncpg
            >>> async def create_pool(settings: PostgresSettings) -> asyncpg.pool.Pool:
            >>>     return await asyncpg.create_pool(
            >>>            dsn=settings.postgres.dsn.get_secret_value(),
            >>>            min_size=settings.postgres.min_size,
            >>>            max_size=settings.postgres.max_size,
            >>>            statement_cache_size=settings.postgres.statement_cache_size,
            >>>     )

        Пример использования с SQLAlchemy:

            >>> import sqlalchemy
            >>> async def create_pool(settings: PostgresSettings) -> sqlalchemy.ext.asyncio.AsyncEngine:
            >>>     return sqlalchemy.ext.asyncio.create_async_engine(
            >>>         settings.postgres.dsn.get_secret_value()
            >>>     )
        """
        return SecretStr(
            f'{self.driver}://{self.user}:{quote(self.password.get_secret_value())}@{self.host}:{self.port}/{self.database}',
        )

    @model_validator(mode='before')
    @classmethod
    def __parse_dsn(cls, values: dict[str, Any]) -> dict[str, Any]:
        dsn = values.get('dsn')
        if dsn is not None and not isinstance(dsn, str):
            msg = "Field 'dsn' must be str"
            raise TypeError(msg)
        if not dsn:
            return values
        parsed_dsn = urlparse(dsn)
        values['driver'] = parsed_dsn.scheme
        values['host'] = parsed_dsn.hostname
        values['port'] = parsed_dsn.port
        values['user'] = parsed_dsn.username
        values['password'] = parsed_dsn.password
        values['database'] = parsed_dsn.path.removeprefix('/')
        return values


class APISettings(BaseModel):
    host: str = '0.0.0.0'  # noqa: S104
    port: int = 8000
    token: SecretStr = SecretStr('supersecret')


class Settings(pydantic_settings.BaseSettings):
    api: APISettings = APISettings()
    postgres: PostgresSettings

    model_config = pydantic_settings.SettingsConfigDict(
        env_nested_delimiter='__',
        env_prefix='TASKIQ_DASHBOARD__',
        env_file=('conf/.env', os.getenv('ENV_FILE', '.env')),
        env_file_encoding='utf-8',
    )
