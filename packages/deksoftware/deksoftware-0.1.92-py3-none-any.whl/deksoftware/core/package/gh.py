from dekartifacts.artifacts.staticfiles import StaticfilesRepoArtifact
from .base import PackageBase, register_package


@register_package('gh')
class GithubPagesPackage(PackageBase):
    artifact_cls = StaticfilesRepoArtifact

    @property
    def registry(self):
        return self.args[0]
