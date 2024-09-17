import tests.fixtures
from tests.helpers import package_paths_in_module

pytest_plugins = [*package_paths_in_module(tests.fixtures)]  # type: ignore
