import requests

from s3s_express.constants import GRAPH_QL_REFERENCE_URL


def get_hashes() -> dict[str, str]:
    """Gets the hashes for the GraphQL queries.

    Returns:
        dict[str, str]: The hashes for the GraphQL queries.
    """
    response = requests.get(GRAPH_QL_REFERENCE_URL)
    hash_map = response.json()["graphql"]["hash_map"]
    return hash_map
