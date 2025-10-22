from typing import override

from liblaf.cherries import core, plugins

from ._abc import Profile


class ProfileDefault(Profile):
    @override  # impl Profile
    def init(self) -> core.Run:
        run: core.Run = core.active_run
        run.register(plugins.Comet())
        run.register(plugins.Git())
        run.register(plugins.Local())
        run.register(plugins.Logging())
        return run
