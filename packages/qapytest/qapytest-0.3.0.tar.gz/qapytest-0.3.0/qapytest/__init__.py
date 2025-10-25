"""QAPyTest is a powerful package for QA specialists built on top of Pytest."""

from faker import Faker

from qapytest._attach import attach
from qapytest._client_http import GraphQLClient, HttpClient
from qapytest._json_validation import validate_json
from qapytest._redis import RedisClient
from qapytest._soft_assert import soft_assert
from qapytest._sql import SqlClient
from qapytest._step import step

__all__ = [
    "Faker",
    "GraphQLClient",
    "HttpClient",
    "RedisClient",
    "SqlClient",
    "attach",
    "soft_assert",
    "step",
    "validate_json",
]
