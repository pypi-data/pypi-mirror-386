import ckan.plugins.toolkit as tk

CONF_DEFAULT_THEME = "ckanext.json_viewer.default_theme"
CONF_DEFAULT_VIEW_NAME = "ckanext.json_viewer.default_view_name"
CONF_DEFAULT_DESCRIPTION = "ckanext.json_viewer.default_description"
CONF_DEFAULT_MAX_HEIGHT = "ckanext.json_viewer.default_max_height"
CONF_DEFAULT_EXPAND = "ckanext.json_viewer.default_expand"
CONF_DEFAULT_INDENTATION = "ckanext.json_viewer.default_indentation"
CONF_DEFAULT_SHOW_DATA_TYPES = "ckanext.json_viewer.default_show_data_types"
CONF_DEFAULT_SHOW_TOOLBAR = "ckanext.json_viewer.default_show_toolbar"
CONF_DEFAULT_SHOW_COPY_BUTTON = "ckanext.json_viewer.default_show_copy_button"
CONF_DEFAULT_SHOW_SIZES = "ckanext.json_viewer.default_show_sizes"


class ExtConfig:
    """Configuration options for the JSON Viewer extension."""

    @classmethod
    def get_default_theme(cls) -> str:
        return tk.config[CONF_DEFAULT_THEME]

    @classmethod
    def get_default_view_name(cls) -> str:
        return tk.config[CONF_DEFAULT_VIEW_NAME]

    @classmethod
    def get_default_description(cls) -> str:
        return tk.config[CONF_DEFAULT_DESCRIPTION]

    @classmethod
    def get_default_max_height(cls) -> int:
        return tk.config[CONF_DEFAULT_MAX_HEIGHT]

    @classmethod
    def get_default_expand(cls) -> bool:
        return tk.asbool(tk.config[CONF_DEFAULT_EXPAND])

    @classmethod
    def get_default_indentation(cls) -> int:
        return tk.config[CONF_DEFAULT_INDENTATION]

    @classmethod
    def get_default_show_data_types(cls) -> bool:
        return tk.asbool(tk.config[CONF_DEFAULT_SHOW_DATA_TYPES])

    @classmethod
    def get_default_show_toolbar(cls) -> bool:
        return tk.asbool(tk.config[CONF_DEFAULT_SHOW_TOOLBAR])

    @classmethod
    def get_default_show_copy_button(cls) -> bool:
        return tk.asbool(tk.config[CONF_DEFAULT_SHOW_COPY_BUTTON])

    @classmethod
    def get_default_show_sizes(cls) -> bool:
        return tk.asbool(tk.config[CONF_DEFAULT_SHOW_SIZES])
