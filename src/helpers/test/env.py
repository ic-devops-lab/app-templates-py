import os
from dataclasses import asdict, dataclass


@dataclass(kw_only=True)
class TestEnv:
    __test__ = False

    app_name: str = "test_app"
    app_version: str = "test_version"
    app_env: str = "test_env"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_workers_count: int = 1

    log_level: str = "DEBUG"

    postgres_enabled: bool = False
    postgres_url: str | None = None

    def get_env_dict(self) -> dict[str, object]:
        return asdict(self)

    def export_env(self) -> None:
        for key, value in self.get_env_dict().items():
            if value is None:
                os.environ.pop(key.upper(), None)
            else:
                os.environ[key.upper()] = str(value)


@dataclass(kw_only=True)
class ProdLikeTestEnv(TestEnv):
    app_name: str = "test_prod_like_app"
    app_env: str = "prod_like_test_env"
    api_reload: bool = False
    api_workers_count: int = 2
    log_level: str = "INFO"


@dataclass(kw_only=True)
class PostgresTestEnv(TestEnv):
    postgres_enabled: bool = True
