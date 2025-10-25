import os

import gixy
from gixy.plugins.plugin import Plugin


class PluginsManager(object):
    def __init__(self, config=None):
        self.imported = False
        self.config = config
        self._plugins = []

    def import_plugins(self):
        if self.imported:
            return

        files_list = os.listdir(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins")
        )
        for plugin_file in files_list:
            if not plugin_file.endswith(".py") or plugin_file.startswith("_"):
                continue
            __import__(
                "gixy.plugins." + os.path.splitext(plugin_file)[0], None, None, [""]
            )

        self.imported = True

    def init_plugins(self):
        self.import_plugins()

        exclude = self.config.skips if self.config else None
        include = self.config.plugins if self.config else None
        severity = self.config.severity if self.config else None
        for plugin_cls in Plugin.__subclasses__():
            name = plugin_cls.__name__
            # Skip not needed plugins if include list is specified
            if include is not None:
                try:
                    if name not in include:
                        continue
                except TypeError:
                    # include doesn't support membership test, skip this check
                    pass
            # Skip plugins that are explicitly excluded
            if exclude is not None:
                try:
                    if name in exclude:
                        continue
                except TypeError:
                    # exclude doesn't support membership test, skip this check
                    pass
            if severity and not gixy.severity.is_acceptable(
                plugin_cls.severity, severity
            ):
                # Skip plugin by severity level
                continue
            if self.config and self.config.has_for(name):
                options = self.config.get_for(name)
            else:
                options = plugin_cls.options
            self._plugins.append(plugin_cls(options))

    @property
    def plugins(self):
        if not self._plugins:
            self.init_plugins()
        return self._plugins

    @property
    def plugins_classes(self):
        self.import_plugins()
        return Plugin.__subclasses__()

    def get_plugins_descriptions(self):
        return map(lambda a: a.name, self.plugins)

    def audit(self, directive):
        for plugin in self.plugins:
            if plugin.directives and directive.name not in plugin.directives:
                continue
            plugin.audit(directive)

    def post_audit(self, root):
        """Call post_audit on plugins that support full config analysis when full config is detected."""
        if not self._is_full_config(root):
            return
            
        for plugin in self.plugins:
            if plugin.supports_full_config:
                plugin.post_audit(root)

    def _is_full_config(self, root):
        """Detect if this is a full nginx config by checking for http block."""
        # Check if root has an http block child
        for child in root.children:
            if child.name == 'http':
                return True
        return False

    def issues(self):
        result = []
        for plugin in self.plugins:
            if not plugin.issues:
                continue
            result.extend(plugin.issues)
        return result
