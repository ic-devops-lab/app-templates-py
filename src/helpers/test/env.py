import os


class TestEnv:
    __test__ = False

    def __init__(
        self,
        app_name: str = "test_app",
        app_version: str = "test_version",
        app_env: str = "test_env",
        api_host: str = "0.0.0.0",
        api_port: int = 8000,
        api_reload: bool = True,
        api_workers_count: int = 1,
        postgres_enabled: bool = False,
        log_level: str = "DEBUG",
    ) -> None:
        self.app_name = app_name
        self.app_version = app_version
        self.app_env = app_env
        self.api_host = api_host
        self.api_port = api_port
        self.api_reload = api_reload
        self.postgres_enabled = postgres_enabled
        self.api_workers_count = api_workers_count
        self.log_level = log_level

    def get_env_dict(self) -> dict[str, object]:
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "app_env": self.app_env,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "api_reload": self.api_reload,
            "postgres_enabled": self.postgres_enabled,
            "api_workers_count": self.api_workers_count,
            "log_level": self.log_level,
        }

    def export_env(self) -> None:
        for key, value in self.get_env_dict().items():
            os.environ[key.upper()] = str(value)


class ProdLikeTestEnv(TestEnv):
    def __init__(
        self,
        app_name: str = "test_prod_like_app",
        app_version: str = "test_version",
        app_env: str = "prod_like_test_env",
        api_host: str = "0.0.0.0",
        api_port: int = 8000,
        api_reload: bool = False,
        api_workers_count: int = 2,
        postgres_enabled: bool = False,
        log_level: str = "INFO",
    ) -> None:
        super().__init__(
            app_name=app_name,
            app_version=app_version,
            app_env=app_env,
            api_host=api_host,
            api_port=api_port,
            api_reload=api_reload,
            api_workers_count=api_workers_count,
            postgres_enabled=postgres_enabled,
            log_level=log_level,
        )
