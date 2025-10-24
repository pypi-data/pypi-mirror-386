import importlib
from typing import Protocol


class PluginInterface(Protocol):
    """Every plugin must implement this interface.

    A valid register function must register each of its modules with the QUARK plugin manager by calling
    "factory.register()" for each module. The register function must be defined at the top level of the module. This
    is best achieved by providing it in the __init__.py file at the top level of the plugin.

    For more information, see the documentation or use the QUARK plugin template:
    https://github.com/QUARK-framework/QUARK-plugin-template
    """

    @staticmethod
    def register() -> None:
        """Plugin method that registers all its provided modules with the factory.

        This method should be available at the top level of a plugin. See the documentation of factory.register for more
        information.
        """


def _import_plugin(plugin_file: str) -> PluginInterface:
    # Is it really a PluginInterface that is returned here? A: Yes, a PluginInterface provides a register function. In
    # python, modules can also provide functions. The reason for this type annotation is just so the type checker does
    # not complain when register is called in line 32. It cannot enforce that the plugin is actually conforming to the
    # interface
    return importlib.import_module(plugin_file)  # type: ignore


def load_plugins(plugin_files: list[str]) -> None:
    """Import and register the plugins at the path-strings given."""
    for plugin_file in plugin_files:
        plugin = _import_plugin(plugin_file)
        plugin.register()
