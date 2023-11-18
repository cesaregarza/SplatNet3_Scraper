import json
import os

import requests


def get_github_file_content(github_url: str) -> dict:
    """Gets the content of a file from GitHub.

    Given a URL to a file on GitHub, gets the content of the file and returns
    it as a dictionary. Uses the GitHub API to get the content of the file
    instead of scraping the GitHub website.

    Args:
        github_url (str): The URL to the file on GitHub.

    Returns:
        dict: The JSON data from the file.
    """
    path_parts = github_url.split("github.com/")[1].split("/")
    owner = path_parts[0]
    repo = path_parts[1]
    # Skips both "blob" and the branch name
    path = "/".join(path_parts[4:])

    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    headers = {"Accept": "application/vnd.github.v3.raw"}
    if "GITHUB_TOKEN" in os.environ:
        print("Using GitHub token to get file content")
        headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"
    else:
        print("No GitHub token found, using unauthenticated requests")

    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        raise ValueError(f"Failed to get file content: {response.status_code}")
    return response.json()


def parse_splatnet3_app_json(
    json_data: dict,
) -> dict:
    return {
        "version": json_data["web_app_ver"],
        "graphql": {"hash_map": json_data["graphql_queries"]},
    }


def parse_tournament_app_json(
    json_data: dict,
) -> dict:
    return {
        "graphql": {"hash_map": json_data["graphql_queries"]},
    }


if __name__ == "__main__":
    SPLATNET_URL = (
        "https://github.com/nintendoapis/nintendo-app-versions/"
        "blob/main/data/splatnet3-app.json"
    )
    TOURNAMENT_URL = (
        "https://github.com/nintendoapis/nintendo-app-versions/"
        "blob/main/data/tournament-manager-app.json"
    )

    splatnet3_app_json = get_github_file_content(SPLATNET_URL)
    tournament_app_json = get_github_file_content(TOURNAMENT_URL)
    parsed_splatnet3_json = parse_splatnet3_app_json(splatnet3_app_json)
    parsed_tournament_json = parse_tournament_app_json(tournament_app_json)

    # Write the parsed JSON to files
    with open("src/splatnet3_scraper/splatnet3_webview_data.json", "w") as f:
        json.dump(parsed_splatnet3_json, f, indent=4)
        f.write("\n")

    with open("src/splatnet3_scraper/tournament_webview_data.json", "w") as f:
        json.dump(parsed_tournament_json, f, indent=4)
        f.write("\n")
