# ckanext-json-viewer

A CKAN extension that provides an interactive JSON viewer for resource visualization, powered by [json-viewer](https://github.com/andypf/json-viewer).

![view example](doc/image.png)

Features

- Interactive JSON visualization with collapsible tree structure
- Syntax highlighting for better readability
- Easy navigation through complex JSON data
- Seamless integration with CKAN's resource views


## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.9 and earlier | not tested    |
| 2.10+           | yes           |


## Installation

Install from source
```sh
pip install -e .
```

Or use `pip`
```sh
pip install ckanext-json-viewer
```

Enable the plugin and the view in your CKAN config file:
```
ckan.plugins = json_viewer
ckan.views.default_views = json_viewer
```

## Config settings

See [config declaration file](./ckanext/json_viewer/config_declaration.yml)

## Tests

To run the tests, do:
```sh
pytest --ckan-ini=test.ini
```

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
