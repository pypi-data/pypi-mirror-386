import pytest
from arcade_cli.utils import Provider, compute_base_url, compute_login_url, resolve_provider_api_key

DEFAULT_CLOUD_HOST = "cloud.arcade.dev"
DEFAULT_ENGINE_HOST = "api.arcade.dev"
LOCALHOST = "localhost"
DEFAULT_PORT = None
DEFAULT_FORCE_TLS = False
DEFAULT_FORCE_NO_TLS = False


@pytest.mark.parametrize(
    "inputs, expected_output",
    [
        pytest.param(
            {
                "host_input": DEFAULT_ENGINE_HOST,
                "port_input": DEFAULT_PORT,
                "force_tls": DEFAULT_FORCE_TLS,
                "force_no_tls": DEFAULT_FORCE_NO_TLS,
            },
            "https://api.arcade.dev",
            id="default",
        ),
        pytest.param(
            {
                "host_input": LOCALHOST,
                "port_input": DEFAULT_PORT,
                "force_tls": DEFAULT_FORCE_TLS,
                "force_no_tls": DEFAULT_FORCE_NO_TLS,
            },
            "http://localhost:9099",
            id="localhost",
        ),
        pytest.param(
            {
                "host_input": DEFAULT_ENGINE_HOST,
                "port_input": 9099,
                "force_tls": DEFAULT_FORCE_TLS,
                "force_no_tls": DEFAULT_FORCE_NO_TLS,
            },
            "https://api.arcade.dev:9099",
            id="custom port",
        ),
        pytest.param(
            {
                "host_input": LOCALHOST,
                "port_input": 9099,
                "force_tls": DEFAULT_FORCE_TLS,
                "force_no_tls": DEFAULT_FORCE_NO_TLS,
            },
            "http://localhost:9099",
            id="localhost with custom port",
        ),
        pytest.param(
            {
                "host_input": DEFAULT_ENGINE_HOST,
                "port_input": DEFAULT_PORT,
                "force_tls": True,
                "force_no_tls": DEFAULT_FORCE_NO_TLS,
            },
            "https://api.arcade.dev",
            id="force TLS",
        ),
        pytest.param(
            {
                "host_input": LOCALHOST,
                "port_input": DEFAULT_PORT,
                "force_tls": True,
                "force_no_tls": DEFAULT_FORCE_NO_TLS,
            },
            "https://localhost:9099",
            id="localhost with force TLS",
        ),
        pytest.param(
            {
                "host_input": DEFAULT_ENGINE_HOST,
                "port_input": 9099,
                "force_tls": True,
                "force_no_tls": DEFAULT_FORCE_NO_TLS,
            },
            "https://api.arcade.dev:9099",
            id="custom port with force TLS",
        ),
        pytest.param(
            {
                "host_input": LOCALHOST,
                "port_input": 9099,
                "force_tls": True,
                "force_no_tls": DEFAULT_FORCE_NO_TLS,
            },
            "https://localhost:9099",
            id="localhost with custom port and force TLS",
        ),
        pytest.param(
            {
                "host_input": DEFAULT_ENGINE_HOST,
                "port_input": DEFAULT_PORT,
                "force_tls": DEFAULT_FORCE_TLS,
                "force_no_tls": True,
            },
            "http://api.arcade.dev",
            id="force no TLS",
        ),
        pytest.param(
            {
                "host_input": LOCALHOST,
                "port_input": DEFAULT_PORT,
                "force_tls": DEFAULT_FORCE_TLS,
                "force_no_tls": True,
            },
            "http://localhost:9099",
            id="localhost with force no TLS",
        ),
        pytest.param(
            {
                "host_input": DEFAULT_ENGINE_HOST,
                "port_input": 9099,
                "force_tls": DEFAULT_FORCE_TLS,
                "force_no_tls": True,
            },
            "http://api.arcade.dev:9099",
            id="custom port with force no TLS",
        ),
        pytest.param(
            {
                "host_input": LOCALHOST,
                "port_input": 9099,
                "force_tls": DEFAULT_FORCE_TLS,
                "force_no_tls": True,
            },
            "http://localhost:9099",
            id="localhost with custom port and force no TLS",
        ),
        pytest.param(
            {
                "host_input": DEFAULT_ENGINE_HOST,
                "port_input": DEFAULT_PORT,
                "force_tls": True,
                "force_no_tls": True,
            },
            "http://api.arcade.dev",
            id="force TLS and no TLS",
        ),
        pytest.param(
            {
                "host_input": LOCALHOST,
                "port_input": DEFAULT_PORT,
                "force_tls": True,
                "force_no_tls": True,
            },
            "http://localhost:9099",
            id="localhost with force TLS and no TLS",
        ),
        pytest.param(
            {
                "host_input": DEFAULT_ENGINE_HOST,
                "port_input": 9099,
                "force_tls": True,
                "force_no_tls": True,
            },
            "http://api.arcade.dev:9099",
            id="custom port with force TLS and no TLS",
        ),
        pytest.param(
            {
                "host_input": LOCALHOST,
                "port_input": 9099,
                "force_tls": True,
                "force_no_tls": True,
            },
            "http://localhost:9099",
            id="localhost with custom port, force TLS and no TLS",
        ),
        pytest.param(
            {
                "host_input": "arandomhost.com",
                "port_input": DEFAULT_PORT,
                "force_tls": DEFAULT_FORCE_TLS,
                "force_no_tls": DEFAULT_FORCE_NO_TLS,
            },
            "https://arandomhost.com",
            id="random host",
        ),
    ],
)
def test_compute_base_url(inputs: dict, expected_output: str):
    base_url = compute_base_url(
        inputs["force_tls"],
        inputs["force_no_tls"],
        inputs["host_input"],
        inputs["port_input"],
    )

    assert base_url == expected_output


@pytest.mark.parametrize(
    "inputs, expected_output",
    [
        pytest.param(
            {"host_input": DEFAULT_CLOUD_HOST, "port_input": DEFAULT_PORT, "state": "123"},
            "https://cloud.arcade.dev/api/v1/auth/cli_login?callback_uri=http%3A%2F%2Flocalhost%3A9905%2Fcallback&state=123",
            id="default",
        ),
        pytest.param(
            {"host_input": "localhost", "port_input": 9099, "state": "123"},
            "http://localhost:9099/api/v1/auth/cli_login?callback_uri=http%3A%2F%2Flocalhost%3A9905%2Fcallback&state=123",
            id="localhost with custom port",
        ),
        pytest.param(
            {"host_input": "localhost", "port_input": DEFAULT_PORT, "state": "123"},
            "http://localhost:8000/api/v1/auth/cli_login?callback_uri=http%3A%2F%2Flocalhost%3A9905%2Fcallback&state=123",
            id="localhost",
        ),
        pytest.param(
            {"host_input": DEFAULT_CLOUD_HOST, "port_input": 8000, "state": "123"},
            "https://cloud.arcade.dev/api/v1/auth/cli_login?callback_uri=http%3A%2F%2Flocalhost%3A9905%2Fcallback&state=123",
            id="cloud host with an ignored custom port",
        ),
        pytest.param(
            {
                "host_input": DEFAULT_CLOUD_HOST,
                "port_input": DEFAULT_PORT,
                "state": "123",
                "callback_host": "other-host.com/123",
            },
            "https://cloud.arcade.dev/api/v1/auth/cli_login?callback_uri=http%3A%2F%2Fother-host.com%2F123%2Fcallback&state=123",
            id="cloud host with a custom callback host",
        ),
    ],
)
def test_compute_login_url(inputs: dict, expected_output: str):
    callback_host = inputs.get("callback_host")
    login_url = compute_login_url(
        inputs["host_input"], inputs["state"], inputs["port_input"], callback_host
    )

    assert login_url == expected_output


def test_resolve_provider_api_key(monkeypatch):
    resolved_api_key = resolve_provider_api_key(Provider.OPENAI, "123")
    assert resolved_api_key == "123"

    resolved_api_key = resolve_provider_api_key("not-a-provider", None)
    assert resolved_api_key is None

    # Ensure OPENAI_API_KEY is not set in the environment for this test
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    resolved_api_key = resolve_provider_api_key(Provider.OPENAI, None)
    assert resolved_api_key is None
