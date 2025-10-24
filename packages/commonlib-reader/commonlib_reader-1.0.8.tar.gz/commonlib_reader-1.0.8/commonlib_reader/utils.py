import json
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests

from commonlib_reader.connector import get_connector


def get_library_names():
    library_names = get_connector().get_json(url="/api/Library/NameList")
    library_names.sort()
    return library_names


def get_disciplines():
    return get_code("Discipline")


def get_code(code: str, scope: Optional[str] = None, name: Optional[str] = None):
    params = {}
    if scope is not None:
        params["scope"] = scope

    if name is not None:
        params["name"] = name
    return get_code_param(code=code, params=params)


def get_code_param(code, params=None):
    if params is None:
        params = {}

    return get_connector().get_json(f"/api/Code/{code}", params=params)


def query_sql(sql: str):
    return post_sql(sql=sql, take=0, skip=0)


def post_sql(sql: str, take: int = 100, skip: int = 0) -> list:
    """Get json from api/sql endpoint accepting sql queries.

    Args:
        sql (str): SQL query to run
        take (int, optional): Number of results to return. Defaults to 100.
        skip (int, optional): Number of results to skip. Defaults to 0.

    Returns:
        list: List of response from api
    """

    url = urljoin(get_connector().get_url(), "api/sql")
    response = requests.post(
        url=url,
        json={"query": sql, "take": take, "skip": skip},
        headers={"Authorization": "Bearer " + get_connector().get_token()},
    )
    if response.status_code == 200:
        try:
            return response.json()
        except json.JSONDecodeError:
            print(
                f"Warning: {str(url)} returned successfully, but not with a valid json response"
            )
    else:
        print(f"Warning: {str(url)} returned status code {response.status_code}")

    return []


def attributes_list_to_dict(attribute_list: List[Dict]) -> Dict:
    """Convert list of attributes typically returned from commonlib to a normal dictionary.

    Args:
        attribute_list (List[Dict]): List of attributes

    Returns:
        Dict: Dictionary with attribute definitionName as keys.
    """
    d = {}
    for r in attribute_list:
        try:
            d[r["definitionName"]] = r["displayValue"]
        except:
            pass

    return d
