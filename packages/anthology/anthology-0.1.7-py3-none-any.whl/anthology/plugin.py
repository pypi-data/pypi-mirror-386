from poetry.console.application import Application
from poetry.plugins.application_plugin import ApplicationPlugin

from anthology.commands import install, run, version


class AnthologyPlugin(ApplicationPlugin):
    def activate(self, application: Application) -> None:
        application.command_loader.register_factory('anthology install', install)

        application.command_loader.register_factory('anthology run', run)

        application.command_loader.register_factory('anthology version', version)

        application.command_loader.register_factory('antho install', install)

        application.command_loader.register_factory('antho run', run)

        application.command_loader.register_factory('antho version', version)
