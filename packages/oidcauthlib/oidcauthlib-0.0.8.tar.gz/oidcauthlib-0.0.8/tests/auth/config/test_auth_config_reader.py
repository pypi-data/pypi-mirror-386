from oidcauthlib.auth.config.auth_config_reader import AuthConfigReader
from oidcauthlib.auth.config.auth_config import AuthConfig
import pytest
from typing import Any, Dict, List

from oidcauthlib.utilities.environment.environment_variables import EnvironmentVariables


class DummyEnvVars(EnvironmentVariables):
    def __init__(self, providers: List[str], configs: Dict[str, Any]) -> None:
        self._providers: List[str] = providers
        self._configs: Dict[str, Any] = configs

    @property
    def auth_providers(self) -> List[str]:
        return self._providers

    def get(self, key: str, default: Any = None) -> Any:
        return self._configs.get(key, default)

    @property
    def auth_redirect_uri(self) -> str:
        return ""

    @property
    def mongo_db_auth_cache_collection_name(self) -> str:
        return ""

    @property
    def mongo_db_cache_disable_delete(self) -> bool:
        return False

    @property
    def mongo_url(self) -> str:
        return ""

    @property
    def mongo_db_name(self) -> str:
        return ""

    @property
    def oauth_cache(self) -> str:
        return ""

    @property
    def oauth_referring_subject(self) -> str:
        return ""


def test_get_auth_configs_for_all_auth_providers() -> None:
    providers: List[str] = ["a", "b"]
    configs: Dict[str, Any] = {}
    env: DummyEnvVars = DummyEnvVars(providers, configs)
    reader: AuthConfigReader = AuthConfigReader(environment_variables=env)

    def dummy_get_config_for_auth_provider(auth_provider: str) -> AuthConfig:
        return AuthConfig(
            auth_provider=auth_provider,
            audience="aud",
            issuer="iss",
            client_id=None,
            client_secret=None,
            well_known_uri=None,
        )

    setattr(reader, "get_config_for_auth_provider", dummy_get_config_for_auth_provider)
    configs_list: List[AuthConfig] = reader.get_auth_configs_for_all_auth_providers()
    assert len(configs_list) == 2
    assert configs_list[0].auth_provider == "a"
    assert configs_list[1].auth_provider == "b"


def test_init_type_and_value_errors() -> None:
    with pytest.raises(ValueError):
        AuthConfigReader(environment_variables=None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        AuthConfigReader(environment_variables=object())  # type: ignore[arg-type]
