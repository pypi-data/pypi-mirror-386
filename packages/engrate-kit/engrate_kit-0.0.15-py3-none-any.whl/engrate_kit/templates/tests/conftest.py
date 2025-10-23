pytest_plugins = ["engrate_kit.testing.fixtures"]


def pytest_configure(config):
    """Pass the app module name to the fixtures."""
    config.app_module_name = "{{app_module_name}}"
