from aiware.client.client import Aiware
from aiware.common.auth import AiwareSessionToken, TokenAuth

def test_client_urls():
    client = Aiware(
        base_url="https://api.us-1.veritone.com"
    )
    assert client.base_url == "https://api.us-1.veritone.com"
    assert client.graphql_url == "https://api.us-1.veritone.com/v3/graphql"
    assert client.search_url == "https://api.us-1.veritone.com/api/search"

def test_client_urls_wildcard():
    client = Aiware(
        base_url="https://api.some-host.com"
    )
    assert client.base_url == "https://api.some-host.com"
    assert client.graphql_url == "https://api.some-host.com/v3/graphql"
    assert client.search_url == "https://api.some-host.com/api/search"

def test_client_with_auth_new_instance():
    original_client = Aiware(
        base_url="https://api.us-1.veritone.com",
        auth=None
    )
    assert original_client.auth is None

    auth = TokenAuth(token=AiwareSessionToken("foo"))
    new_client = original_client.with_auth(auth)
    
    assert new_client is not original_client

    # original auth is still None
    assert original_client.auth is None
    assert new_client.auth is auth
