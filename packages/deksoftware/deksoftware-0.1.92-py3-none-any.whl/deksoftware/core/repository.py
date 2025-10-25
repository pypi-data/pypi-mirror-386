from dektools.file import remove_path
from dektools.serializer.yaml import yaml
from .package.base import all_package, path_resources
from .installer.base import all_installer


class Repository:
    def __init__(self, typed=None, *args):
        self.packages = {}
        self.load(path_resources / 'index.yaml', typed or 'default', *args)

    def load(self, path, typed, *args):
        package_cls = all_package[typed]
        meta = yaml.load(path)
        for data in meta.get('packages', []):
            package = package_cls(data, *args)
            self.packages[package.name] = package

    def pull(self, name, version):
        return self.packages[name].pull(version)

    def install(self, name, version=None, path=None, extra=None):
        path_final = path or self.pull(name, version or '0.1.0')
        installer_cls = all_installer[name]
        installer_cls(path_final, extra).run()
        if not path:
            remove_path(path_final)
