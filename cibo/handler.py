from typing import Callable, Dict, List, Optional, Set, Type

from flask.views import MethodView
from pydantic import BaseModel
from typing_extensions import Literal

from .context import Context
from .types import TCorsConfig


class Handler(MethodView):

    methods: Set[Literal["GET", "POST", "PUT", "DELETE"]]
    handle_func_name = "handle"
    decorators: List[Callable] = list()
    cors_config: Optional[TCorsConfig] = None

    context_cls: Type[Context] = Context

    Query: Optional[BaseModel] = None
    Body: Optional[BaseModel] = None

    parameters: List[Dict] = list()
    responses: Dict = dict()

    @classmethod
    def as_view(cls, name: str = None, *args, **kwargs):
        if not hasattr(cls, cls.handle_func_name):
            raise ValueError(f"class {cls} does not have {cls.handle_func_name} method")

        if not name:
            name = cls.__name__

        return super().as_view(name, *args, **kwargs)
