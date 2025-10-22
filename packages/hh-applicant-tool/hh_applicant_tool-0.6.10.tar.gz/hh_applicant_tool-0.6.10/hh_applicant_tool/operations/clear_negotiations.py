# Этот модуль можно использовать как образец для других
import argparse
import logging
from datetime import datetime, timedelta, timezone

from ..api import ApiClient, ClientError
from ..constants import INVALID_ISO8601_FORMAT
from ..main import BaseOperation
from ..main import Namespace as BaseNamespace
from ..types import ApiListResponse
from ..utils import print_err, truncate_string

logger = logging.getLogger(__package__)


class Namespace(BaseNamespace):
    older_than: int
    blacklist_discard: bool
    all: bool


class Operation(BaseOperation):
    """Отменяет старые отклики, скрывает отказы с опциональной блокировкой работодателя."""

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--older-than",
            type=int,
            default=30,
            help="Удалить отклики старше опр. кол-ва дней. По умолчанию: %(default)d",
        )
        parser.add_argument(
            "--all",
            type=bool,
            default=False,
            action=argparse.BooleanOptionalAction,
            help="Удалить все отклики в тч с приглашениями",
        )
        parser.add_argument(
            "--blacklist-discard",
            help="Если установлен, то заблокирует работодателя в случае отказа, чтобы его вакансии не отображались в возможных",
            type=bool,
            default=False,
            action=argparse.BooleanOptionalAction,
        )

    def _get_active_negotiations(self, api_client: ApiClient) -> list[dict]:
        rv = []
        page = 0
        per_page = 100
        while True:
            r: ApiListResponse = api_client.get(
                "/negotiations", page=page, per_page=per_page, status="active"
            )
            rv.extend(r["items"])
            page += 1
            if page >= r["pages"]:
                break
        return rv

    def run(self, args: Namespace, api_client: ApiClient, *_) -> None:
        negotiations = self._get_active_negotiations(api_client)
        print("Всего активных:", len(negotiations))
        for item in negotiations:
            state = item["state"]
            # messaging_status archived
            # decline_allowed False
            # hidden True
            is_discard = state["id"] == "discard"
            if not item["hidden"] and (
                args.all
                or is_discard
                or (
                    state["id"] == "response"
                    and (datetime.utcnow() - timedelta(days=args.older_than)).replace(
                        tzinfo=timezone.utc
                    )
                    > datetime.strptime(item["updated_at"], INVALID_ISO8601_FORMAT)
                )
            ):
                decline_allowed = item.get("decline_allowed") or False
                r = api_client.delete(
                    f"/negotiations/active/{item['id']}",
                    with_decline_message=decline_allowed,
                )
                assert {} == r
                vacancy = item["vacancy"]
                print(
                    "❌ Удалили",
                    state["name"].lower(),
                    vacancy["alternate_url"],
                    "(",
                    truncate_string(vacancy["name"]),
                    ")",
                )
                if is_discard and args.blacklist_discard:
                    employer = vacancy.get("employer", {})
                    if not employer or 'id' not in employer:
                        # Работодатель удален или скрыт
                        continue
                    try:
                        r = api_client.put(f"/employers/blacklisted/{employer['id']}")
                        assert not r
                        print(
                            "🚫 Заблокировали",
                            employer["alternate_url"],
                            "(",
                            truncate_string(employer["name"]),
                            ")",
                        )
                    except ClientError as ex:
                        print_err("❗ Ошибка:", ex)
        print("🧹 Чистка заявок завершена!")
