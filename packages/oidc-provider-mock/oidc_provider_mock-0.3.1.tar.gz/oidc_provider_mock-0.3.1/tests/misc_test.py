import inspect
from collections.abc import Callable
from http import HTTPStatus

import flask.testing

import oidc_provider_mock
import oidc_provider_mock._app

from .conftest import use_provider_config


def test_userinfo_unauthorized(client: flask.testing.FlaskClient):
    response = client.get("/userinfo")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.www_authenticate.type == "bearer"
    assert response.json
    assert response.json["error"] == "missing_authorization"

    response = client.get("/userinfo", headers={"authorization": "foo"})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json == {"error": "unsupported_token_type"}

    response = client.get("/userinfo", headers={"authorization": "Bearer foo"})
    # Should be `HTTPStatus.UNAUTHORIZED` but there is a bug in authlib
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json
    assert response.json["error"] == "access_denied"


def test_consistent_kwargs():
    """Check that kwargs for configuring the provider are consistent across all APIs"""

    def kw_only_params(obj: Callable[..., object]):
        signature = inspect.signature(obj)

        return tuple(
            (k, v.annotation, v.default)
            for k, v in signature.parameters.items()
            if v.kind
            if v.kind == inspect.Parameter.KEYWORD_ONLY
        )

    expected_params = kw_only_params(oidc_provider_mock._app.Config)

    assert kw_only_params(oidc_provider_mock.init_app) == expected_params
    assert kw_only_params(oidc_provider_mock.run_server_in_thread) == expected_params
    assert kw_only_params(use_provider_config) == expected_params
