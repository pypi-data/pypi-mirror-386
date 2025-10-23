"""Git hooks package."""

from noveler.infrastructure.git.hooks.plot_version_post_commit import PlotVersionPostCommitHook

__all__ = [
    "PlotVersionPostCommitHook",
]
