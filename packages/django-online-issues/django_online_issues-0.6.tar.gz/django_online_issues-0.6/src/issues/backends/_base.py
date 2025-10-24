from typing import TYPE_CHECKING, Any, TypedDict

from issues.exceptions import IssueError
from issues.forms import IssueFormCleanedData

if TYPE_CHECKING:
    from django.http import HttpRequest

not_provided = object()


class IssueData(TypedDict):
    title: str
    type: str
    description: str


class BaseBackend:
    screenshot_supported: bool = True

    def __init__(self, request: "HttpRequest") -> None:
        self.request = request

    def get_issue_choices(self) -> list[tuple[str, str]]:
        from issues.config import CONFIG

        return [(issue_type, issue_type) for issue_type in CONFIG.TYPES]

    def get_option(self, name: str, default: Any = not_provided) -> Any:
        from issues.config import CONFIG

        try:
            return CONFIG.OPTIONS[name]
        except KeyError as e:
            if default == not_provided:
                raise IssueError("Issues backend Improperly configured.") from e
            return default

    def get_context(self) -> dict[str, Any]:
        from issues.config import CONFIG

        if not CONFIG.ANNOTATIONS:
            pass
        data = {
            "extras": {},
            "url": self.request.META.get("HTTP_REFERER", "N/A"),
            "user": CONFIG.get_annotation("get_user", self.request),
            "user_agent": CONFIG.get_annotation("get_user_agent", self.request),
            "version": CONFIG.get_annotation("get_version", self.request),
            "remote_ip": CONFIG.get_annotation("get_client_ip", self.request),
        }
        data["extras"] = CONFIG.ANNOTATIONS["get_extra_info"](self.request, data)
        return data

    def get_description(self, parameters: dict[str, Any]) -> str:
        from issues.config import CONFIG

        template: str = CONFIG.ISSUE_TEMPLATE
        return template.format(**self.get_context(), **parameters)

    def create_ticket(self, cleaned_data: IssueFormCleanedData) -> bool:
        raise NotImplementedError(f"{self.__class__.__name__} does not implement create_ticket")
