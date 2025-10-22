# Этот модуль можно использовать как образец для других
import argparse
import logging

from prettytable import PrettyTable

from ..api import ApiClient
from ..main import BaseOperation
from ..main import Namespace as BaseNamespace
from ..types import ApiListResponse
from ..utils import truncate_string

logger = logging.getLogger(__package__)


class Namespace(BaseNamespace):
    pass


class Operation(BaseOperation):
    """Список резюме"""

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, args: Namespace, api_client: ApiClient, *_) -> None:
        resumes: ApiListResponse = api_client.get("/resumes/mine")
        t = PrettyTable(field_names=["ID", "Название", "Статус"], align="l", valign="t")
        t.add_rows(
            [
                (
                    x["id"],
                    truncate_string(x["title"]),
                    x["status"]["name"].title(),
                )
                for x in resumes["items"]
            ]
        )
        print(t)
