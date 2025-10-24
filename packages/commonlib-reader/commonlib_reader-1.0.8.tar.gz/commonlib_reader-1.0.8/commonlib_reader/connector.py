from eq_api_connector import APIConnector

_connector = None


def get_connector() -> APIConnector:
    """Get a singleton instance of the APIConnector.

    Returns:
        APIConnector: An instance of the APIConnector class.
    """
    global _connector
    if _connector is None:
        clientID = "728cfddd-b8e9-4ed7-b9a3-8f2fd5b8e79a"
        scopes = ["37d598fc-da0f-46bd-949f-7107918d47a5/user_impersonation"]
        _connector = APIConnector(client_id=clientID, scope=scopes)
        _connector.set_url_prod("https://commonlibapi.equinor.com/")

    return _connector


def set_connector(connector: APIConnector):
    """Set the singleton instance of the APIConnector.

    Args:
        connector (APIConnector): An instance of the APIConnector class.
    """
    global _connector
    _connector = connector
