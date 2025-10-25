from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport


async def graphql(url, email, password):
    client = _create_graphql_client(url)
    bearer = await _get_graphql_bearer(client, email, password)
    client = _create_graphql_client(url, bearer)
    return client


def _create_graphql_client(url, bearer=None):
    transport_params = dict(url=url)
    if bearer is not None:
        transport_params["headers"] = dict(Authorization=f"Bearer {bearer}")

    transport = AIOHTTPTransport(**transport_params)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    return client


async def _get_graphql_bearer(client, email, password):
    query_login = f"""
        mutation login {{
          authenticate(
            input: {{email: "{email}", password: "{password}"}}
          ) {{
            clientMutationId
            jwtToken
          }}
        }}"""
    result_login = await client.execute_async(gql(query_login))
    bearer = result_login["authenticate"]["jwtToken"]
    if not bearer:
        raise Exception("AuthentificationException: Wrong Password?")
    return bearer
