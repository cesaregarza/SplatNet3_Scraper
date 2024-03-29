from unittest import mock

import requests

from splatnet3_scraper.auth.graph_ql_queries import GraphQLQueries
from splatnet3_scraper.constants import (
    DEFAULT_USER_AGENT,
    GRAPHQL_URL,
    SPLATNET_URL,
)

utils_path = "splatnet3_scraper.utils"
graph_ql_path = "splatnet3_scraper.auth.graph_ql_queries"
test_graphql_path = graph_ql_path + ".GraphQLQueries"


class TestGraphQLQueries:
    def test_init(self):
        queries = GraphQLQueries()
        assert isinstance(queries.session, requests.Session)

    @mock.patch(graph_ql_path + ".get_splatnet_version")
    def test_query_header(self, mock_get_version: mock.MagicMock):
        queries = GraphQLQueries()
        expected_bullet_token = "test_bullet_token"
        expected_language = "test_language"
        expected_splatnet_web_version = "test_version"
        override = {"test_key": "test_value"}
        expected_header = {
            "Authorization": f"Bearer {expected_bullet_token}",
            "Accept-Language": expected_language,
            "User-Agent": DEFAULT_USER_AGENT,
            "X-Web-View-Ver": expected_splatnet_web_version,
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": SPLATNET_URL,
            "X-Requested-With": "com.nintendo.znca",
            "Referer": (
                f"{SPLATNET_URL}?"
                f"lang={expected_language}"
                f"&na_country={expected_language[-2:]}"
                f"&na_lang={expected_language}"
            ),
            "Accept-Encoding": "gzip, deflate",
            "test_key": "test_value",
        }
        mock_get_version.return_value = expected_splatnet_web_version
        header = queries.query_header(
            expected_bullet_token,
            expected_language,
            override=override,
        )
        assert header == expected_header

    def test_query_body_hash(self):
        queries = GraphQLQueries()
        query_hash = "test_hash"
        variables = {"test_variable": "test_value"}
        expected_call = {
            "extensions": {
                "persistedQuery": {
                    "sha256Hash": query_hash,
                    "version": 1,
                }
            },
            "variables": variables,
        }
        with mock.patch("json.dumps") as mock_dumps:
            mock_dumps.return_value = "test_json"
            body = queries.query_body_hash(query_hash, variables)
        mock_dumps.assert_called_once_with(expected_call)
        assert body == "test_json"

    def test_query_body(self):
        queries = GraphQLQueries()
        query_name = "anarchy"
        variables = {"test_variable": "test_value"}
        with (
            mock.patch(test_graphql_path + ".get_query") as mock_get_query,
            mock.patch(
                test_graphql_path + ".query_body_hash"
            ) as mock_query_body_hash,
        ):
            mock_get_query.return_value = "test_query"
            mock_query_body_hash.return_value = "test_body"
            body = queries.query_body(query_name, variables)
        mock_get_query.assert_called_once_with(query_name)
        mock_query_body_hash.assert_called_once_with("test_query", variables)
        assert body == "test_body"

    def test_query_hash(self):
        queries = GraphQLQueries()
        query_hash = "test_hash"
        bullet_token = "test_bullet_token"
        gtoken = "test_gtoken"
        language = "test_language"
        user_agent = "test_user_agent"
        override = {"test_key": "test_value_override"}
        variables = {"test_variable": "test_value_variable"}

        with (
            mock.patch(
                test_graphql_path + ".query_header"
            ) as mock_query_header,
            mock.patch(
                test_graphql_path + ".query_body_hash"
            ) as mock_query_body,
            mock.patch("requests.Session.post") as mock_post,
        ):
            mock_query_header.return_value = "test_header"
            mock_query_body.return_value = "test_body"
            mock_post.return_value = "test_response"
            response = queries.query_hash(
                query_hash,
                bullet_token,
                gtoken,
                language,
                user_agent,
                override=override,
                variables=variables,
            )
            mock_query_header.assert_called_once_with(
                bullet_token,
                language,
                user_agent,
                override,
            )
            mock_query_body.assert_called_once_with(query_hash, variables)
            mock_post.assert_called_once_with(
                GRAPHQL_URL,
                headers="test_header",
                data="test_body",
                cookies={"_gtoken": gtoken},
            )
            assert response == "test_response"

    def test_query(self):
        queries = GraphQLQueries()
        query_name = "anarchy"
        bullet_token = "test_bullet_token"
        gtoken = "test_gtoken"
        language = "test_language"
        user_agent = "test_user_agent"
        variables = {"test_variable": "test_value_variable"}
        override = {"test_key": "test_value_override"}

        with (
            mock.patch(test_graphql_path + ".query_hash") as mock_query_hash,
            mock.patch(test_graphql_path + ".get_query") as mock_get_query,
        ):
            mock_get_query.return_value = "test_query"
            mock_query_hash.return_value = "test_response"
            response = queries.query(
                query_name,
                bullet_token,
                gtoken,
                language,
                user_agent,
                variables,
                override,
            )
            mock_get_query.assert_called_once_with(query_name)
            mock_query_hash.assert_called_once_with(
                "test_query",
                bullet_token,
                gtoken,
                language,
                user_agent,
                variables,
                override,
            )
            assert response == "test_response"
