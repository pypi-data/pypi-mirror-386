from __future__ import annotations

from ckanext.json_viewer import config


def json_viewer_get_default_theme() -> str:
    return config.get_default_theme()


def json_viewer_get_default_max_height() -> int:
    return config.get_default_max_height()


def json_viewer_get_theme_options() -> list[dict[str, str]]:
    return [
        {"value": theme, "text": theme}
        for theme in [
            "apathyashes",
            "atelier-dune-light",
            "atelier-dune",
            "atlas",
            "bespin",
            "black-metal",
            "brewer",
            "bright",
            "brogrammer",
            "brushtrees-dark",
            "brushtrees",
            "chalk",
            "circus",
            "classic-dark",
            "classic-light",
            "codeschool",
            "cupcake",
            "cupertino",
            "darcula",
            "darktooth",
            "default-dark",
            "default-light",
            "dracula",
            "eighties",
            "embers",
            "flat",
            "fruit-soda",
            "github",
            "google-dark",
            "google-light",
            "grayscale-dark",
            "grayscale-light",
            "greenscreen",
            "gruvbox-dark-hard",
            "gruvbox-light-hard",
            "harmonic-dark",
            "harmonic-light",
            "heetch-light",
            "heetch",
            "helios",
            "hopscotch",
            "horizon-dark",
            "ia-dark",
            "ia-light",
            "icy",
            "isotope",
            "macintosh",
            "marrakesh",
            "materia",
            "material-lighter",
            "material",
            "mellow-purple",
            "mexico-light",
            "mocha",
            "monokai",
            "nord",
            "ocean",
            "one-light",
            "onedark",
            "papercolor-dark",
            "papercolor-light",
            "paraiso",
            "pico",
            "pop",
            "railscasts",
            "seti",
            "solarized-dark",
            "solarized-light",
            "spacemacs",
            "summerfruit-dark",
            "summerfruit-light",
            "tomorrow-night",
            "tomorrow",
            "tube",
            "twilight",
            "woodland",
            "zenburn",
        ]
    ]
