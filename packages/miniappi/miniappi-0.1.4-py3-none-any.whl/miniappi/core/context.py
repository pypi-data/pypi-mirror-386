from copy import copy
from typing import TYPE_CHECKING, Any, Dict, Union
from dataclasses import dataclass, field
from miniappi.core.models.context import ContextModel

if TYPE_CHECKING:
    from .models.content import BaseContent
    from . import App, Session


@dataclass
class CurrentContent:
    root: Union["BaseContent", None] = None
    references: Dict[str, "BaseContent"] = field(default_factory=lambda: {})

class UserContext(ContextModel):

    session: "Session" # Current stream session
    request_id: str
    extra: dict = field(default_factory=lambda: {})

    def copy(self):
        return copy(self)

class AppContext(ContextModel):

    app: "App"
    app_name: str
    app_url: str
    sessions: Dict[str, "Session"]
    extra: dict = field(default_factory=lambda: {})

    def copy(self):
        return copy(self)

user_context = UserContext()
app_context = AppContext()
