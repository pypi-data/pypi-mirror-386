from shai_plugin.core.entities.plugin.setup import PluginArch, PluginConfiguration, PluginLanguage


def test_optional_minimum_shai_required():
    meta = PluginConfiguration.Meta(
        version="1.0.0",
        arch=[PluginArch.AMD64, PluginArch.ARM64],
        runner=PluginConfiguration.Meta.PluginRunner(
            language=PluginLanguage.PYTHON, version="3.10", entrypoint="main.py"
        ),
        minimum_shai_version="1.0.0",
    )

    assert meta.minimum_shai_version == "1.0.0"

    meta = PluginConfiguration.Meta(
        version="1.0.0",
        arch=[PluginArch.AMD64, PluginArch.ARM64],
        runner=PluginConfiguration.Meta.PluginRunner(
            language=PluginLanguage.PYTHON, version="3.10", entrypoint="main.py"
        ),
    )

    assert meta.minimum_shai_version is None
