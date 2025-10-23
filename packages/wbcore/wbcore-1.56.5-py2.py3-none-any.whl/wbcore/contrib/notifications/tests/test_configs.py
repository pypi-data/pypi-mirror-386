from wbcore.configs.registry import ConfigRegistry


def test_notifications_config(config_registry: ConfigRegistry):
    notifications = config_registry.get_config_dict()["notifications"]
    assert notifications["endpoint"]
    assert notifications["token"]
