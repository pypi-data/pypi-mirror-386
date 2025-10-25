import pytest

from dynaconf import Dynaconf

from roboherd.cow import RoboCow

from .config import CowConfig, HerdConfig


@pytest.fixture
def test_config():
    config = Dynaconf()
    config.update(
        {
            "cow": {
                "moocow": {
                    "bot": "moocow:bot",
                },
                "rooster": {
                    "bot": "rooster:bot",
                },
            },
        }
    )  # type: ignore
    return config


def test_from_name_and_dict():
    name = "cow"
    value = {
        "bot": "module:attribute",
    }

    cow = CowConfig.from_name_and_dict(name, value)

    assert cow.name == name
    assert cow.module == "module"
    assert cow.attribute == "attribute"


def test_from_name_and_dict_with_new_name():
    name = "cow"
    value = {
        "bot": "roboherd.examples.moocow:moocow",
        "handle": "new_handle",
        "name": "new name",
        "skip_profile_update": True,
    }

    config = CowConfig.from_name_and_dict(name, value)

    cow = config.load()

    assert cow.information.name == "new name"
    assert cow.information.handle == "new_handle"
    assert cow.skip_profile_update is True


def test_load_config(test_config):
    herd = HerdConfig.from_settings(test_config)

    assert len(herd.cows) == 2

    moocow = herd.for_name("moocow")
    assert moocow
    assert moocow.name == "moocow"


def test_load_from_cow_config():
    name = "cow"
    value = {
        "bot": "roboherd.examples.moocow:moocow",
    }

    cow = CowConfig.from_name_and_dict(name, value)

    assert isinstance(cow.load(), RoboCow)


def test_names(test_config):
    herd = HerdConfig.from_settings(test_config)

    assert herd.names == {"moocow", "rooster"}
