from typing import Any, Dict, List, Optional, Union

from apispec import APISpec
from flask import Blueprint
from flask import Flask as _Flask
from flask import render_template_string

from cibo.handler import Handler

from .ui_templates import DOCS_TEMPLATE, OAUTH2_REDIRECT_TEMPLATE, REDOC_TEMPLATE


class Flask(_Flask):
    openapi_version: str
    tags: List

    def __init__(
        self,
        import_name: str,
        *,
        static_url_path: Optional[str] = None,
        static_folder: str = "static",
        static_host: Optional[str] = None,
        host_matching: bool = False,
        subdomain_matching: bool = False,
        template_folder: str = "templates",
        instance_path: Optional[str] = None,
        instance_relative_config: bool = False,
        root_path: Optional[str] = None,
        enable_doc: bool = True,
        openapi_url_prefix: str = None,
        # NOTE openapi 相关参数 https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.2.md
        # openapi
        openapi: str = "3.0.2",
        # info
        title: str,
        description: str = None,
        terms_of_service: str = None,
        contact: Dict = None,
        license: Dict = None,
        version: str,
        # servers
        servers: List[Dict] = None,
        # paths
        # components
        # security
        # tags
        # externalDocs
        external_docs: Dict = None,
        docs_path: str = "/docs",
        docs_oauth2_redirect_path: str = "/docs/oauth2-redirect",
        redoc_path: str = "/redoc",
        spec_path: str = "/openapi.json",
    ) -> None:
        super().__init__(
            import_name,
            static_url_path=static_url_path,
            static_folder=static_folder,
            static_host=static_host,
            host_matching=host_matching,
            subdomain_matching=subdomain_matching,
            template_folder=template_folder,
            instance_path=instance_path,
            instance_relative_config=instance_relative_config,
            root_path=root_path,
        )

        self.enable_doc = enable_doc
        self.openapi_url_prefix = openapi_url_prefix
        self.openapi = openapi
        """Info Object 
        https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.2.md#infoObject
        {
            "title": "Sample Pet Store App",
            "description": "This is a sample server for a pet store.",
            "termsOfService": "http://example.com/terms/",
            "contact": {
                "name": "API Support",
                "url": "http://www.example.com/support",
                "email": "support@example.com"
            },
            "license": {
                "name": "Apache 2.0",
                "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
            },
            "version": "1.0.1"
        }
        """
        self.title = title
        self.description = description
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license = license
        self.version = version

        """Servers
        https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.2.md#serverObject
        "servers": [
            {
                "url": "https://{username}.gigantic-server.com:{port}/{basePath}",
                "description": "The production API server",
                "variables": {
                    "username": {
                        "default": "demo",
                        "description": "this value is assigned by the service provider, in this example `gigantic-server.com`"
                    },
                    "port": {
                        "enum": [
                            "8443",
                            "443"
                        ],
                            "default": "8443"
                        },
                        "basePath": {
                            "default": "v2"
                        }
                    }
                }
            }
        ]
        """
        self.servers = servers

        """
        https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.2.md#externalDocumentationObject
        """
        self.external_docs = external_docs

        self.docs_path = docs_path
        self.docs_oauth2_redirect_path = docs_oauth2_redirect_path
        self.redoc_path = redoc_path
        self.spec_path = spec_path
        self._register_openapi_blueprint()

    def _register_openapi_blueprint(self):
        """注册openapi蓝图"""
        bp = Blueprint("_openapi", __name__, url_prefix=self.openapi_url_prefix)
        if self.spec_path:
            """openapi.json"""

            @bp.route(self.spec_path)
            def spec():  # type: ignore
                return self._get_spec(force_update=True)

        if self.docs_path:
            """Swagger"""

            @bp.route(self.docs_path)
            def docs() -> str:  # type: ignore
                return render_template_string(
                    DOCS_TEMPLATE, oauth2_redirect_path=self.docs_oauth2_redirect_path
                )

        if self.docs_oauth2_redirect_path:

            @bp.route(self.docs_oauth2_redirect_path)
            def oauth_redirect() -> str:  # type: ignore
                return render_template_string(OAUTH2_REDIRECT_TEMPLATE)

        if self.redoc_path:
            """Redoc"""

            @bp.route(self.redoc_path)
            def redoc() -> str:  # type: ignore
                return render_template_string(REDOC_TEMPLATE)

        if self.enable_doc and (self.docs_path or self.redoc_path):
            self.register_blueprint(bp)

    def _get_spec(self, spec_format: str = "json", force_update=False) -> Union[dict, str]:
        if not force_update and self._spec:
            return self._spec

        if spec_format == "json":
            self._spec = self._generate_spec().to_dict()
        else:
            self._spec = self._generate_spec().to_yaml()

        return self._spec

    def _generate_spec(self) -> APISpec:
        kwargs = {}
        if self.servers:
            kwargs["servers"] = self.servers
        if self.external_docs:
            kwargs["external_docs"] = self.external_docs
        spec: APISpec = APISpec(
            title=self.title,
            version=self.version,
            openapi_version=self.openapi,
            info=self._make_info(),
            tags=self._make_tags(),
            paths=self._make_paths(),
            **kwargs,
        )

        return spec

    def _make_info(self) -> dict:
        """Make OpenAPI info object."""
        info: dict
        info = {}
        if self.contact:
            info["contact"] = self.contact
        if self.license:
            info["license"] = self.license
        if self.terms_of_service:
            info["termsOfService"] = self.terms_of_service
        if self.description:
            info["description"] = self.description
        return info

    def _make_tags(self) -> List[Dict[str, Any]]:
        """Make OpenAPI tags object."""
        tags = list()
        for blueprint_name, blueprint in self.blueprints.items():
            if blueprint_name == "_openapi":
                continue
            tag: Dict[str, Any] = get_tag(blueprint, blueprint_name)
            tags.append(tag)
        return tags

    def _make_paths(self) -> dict:
        paths = {}
        for rule in self.url_map.iter_rules():
            view_func = self.view_functions[rule.endpoint]
            if hasattr(view_func, "view_class") and issubclass(view_func.view_class, Handler):
                class_ = view_func.view_class
                func = getattr(class_, class_.handle_func_name)
                if not func:
                    raise AttributeError(
                        f"{class_.__name__} must have function {class_.handle_func_name}"
                    )
                for method in class_.methods:
                    paths[rule.rule] = {
                        method.lower(): {
                            "tags": ["api"],
                            "summary": func.__doc__,
                            "parameters": class_.parameters,
                            "responses": class_.responses,
                        }
                    }
        return paths


def get_tag(blueprint, blueprint_name: str) -> Dict[str, Any]:
    """Get tag from blueprint object."""
    tag: Dict[str, Any]
    if isinstance(blueprint.openapi_tag, dict):
        tag = blueprint.openapi_tag
    else:
        tag = {"name": blueprint.openapi_tag}
    return tag