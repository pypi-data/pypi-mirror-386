from typing import Any

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import types
from ckan.common import CKANConfig

import ckanext.resourceproxy.plugin as proxy

from ckanext.json_viewer.config import ExtConfig
from ckanext.json_viewer.logic.schema import get_preview_schema


@tk.blanket.helpers
@tk.blanket.config_declarations
class JsonViewerPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IResourceView, inherit=True)

    # IConfigurer

    def update_config(self, config_: CKANConfig):
        tk.add_template_directory(config_, "templates")
        tk.add_resource("assets", "json_viewer")

    # IResourceView

    def info(self) -> dict[str, Any]:
        return {
            "name": "json_viewer",
            "title": "JSON Viewer",
            "icon": "fa fa-code",
            "iframed": False,
            "schema": get_preview_schema(),
            "preview_enabled": True,
            "default_title": ExtConfig.get_default_view_name(),
            "default_description": ExtConfig.get_default_description(),
        }

    def can_view(self, data_dict: dict[str, Any]) -> bool:
        return data_dict["resource"].get("format", "").lower() == "json"

    def setup_template_variables(
        self, context: types.Context, data_dict: dict[str, Any]
    ):
        default_view_data = {
            "title": ExtConfig.get_default_view_name(),
            "description": ExtConfig.get_default_description(),
            "max_height": ExtConfig.get_default_max_height(),
            "theme": ExtConfig.get_default_theme(),
            "expand": ExtConfig.get_default_expand(),
            "indentation": ExtConfig.get_default_indentation(),
            "show_data_types": ExtConfig.get_default_show_data_types(),
            "show_toolbar": ExtConfig.get_default_show_toolbar(),
            "show_copy_button": ExtConfig.get_default_show_copy_button(),
            "show_sizes": ExtConfig.get_default_show_sizes(),
        }

        for key, value in default_view_data.items():
            data_dict["resource_view"].setdefault(key, value)

        data_dict["resource_url"] = proxy.get_proxified_resource_url(data_dict)

        return data_dict

    def view_template(self, context: types.Context, data_dict: dict[str, Any]):
        return "json_view.html"

    def form_template(self, context: types.Context, data_dict: dict[str, Any]):
        return "json_form.html"
