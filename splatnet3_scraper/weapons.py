import json
import re
from functools import cache, cached_property
from typing import Any, TypeAlias

import requests

RAW_URL = "https://raw.githubusercontent.com/"
DATA_URL = (
    "https://raw.githubusercontent.com//Leanny/leanny.github.io/master/splat3"
    "/data/mush/"
)
VERSION_URL = (
    "https://github.com/Leanny/leanny.github.io/tree/master/splat3/data/mush"
)
LANG_URL = "Leanny/leanny.github.io/master/splat3/data/language/"

WeaponsMap: TypeAlias = dict[str, dict[str, str | float]]

version_regex = re.compile(r"Link--primary\" title=\"(\d{3})")


@cache
def enumerate_versions() -> list[str]:
    """Get a list of all the versions of the datamine. If return_soup is True,
    return the BeautifulSoup ResultSet instead.

    Args:
        return_soup (bool): Whether to return the BeautifulSoup ResultSet. If
            False, return a list of the versions. Defaults to False.

    Returns:
        list[str] | ResultSet: The versions of the datamine.
    """
    response = requests.get(VERSION_URL)
    return version_regex.findall(response.text)


@cache
def get_version_url(version: str | None = None) -> str:
    """Get the URL for the specified version of the datamine. If no version is
    specified, get the latest version. If the version is not found, return the
    previous version.

    Args:
        version (str | None): The version to get the URL for. If None, get the
            latest version. Defaults to None.

    Returns:
        str: The URL for the specified version.
    """
    versions = enumerate_versions()
    versions_text = [(version, i) for i, version in enumerate(versions)]
    versions_text.sort(key=lambda x: x[0])
    if version is None:
        selected_version_idx = versions_text[-1][1]
    else:
        version = version.replace("v", "").replace(".", "")
        # Leanny's datamine does not include changes that do not affect gameplay
        # such as bug fixes, so we get the highest version that is less than or
        # equal to the specified version.
        selected_version_idx = [i for v, i in versions_text if v <= version][-1]
    selected_version = versions[selected_version_idx]
    out_url: str = DATA_URL + selected_version
    return out_url


@cache
def get_weapon_data(version: str | None = None) -> dict:
    """Get the weapon data from the specified version of the datamine. If no
    version is specified, get the latest version.

    Args:
        version (str | None): The version to get the data from. If None, get the
            latest version. Defaults to None.

    Returns:
        dict: The weapon data.
    """
    url = get_version_url(version=version) + "/WeaponInfoMain.json"
    response = requests.get(url)
    return response.json()


@cache
def get_language_data(lang: str = "USen") -> dict:
    """Get the language data for the specified language.

    Args:
        lang (str): The language to get the data for. Defaults to "USen".

    Returns:
        dict: The language data.
    """
    response = requests.get(RAW_URL + LANG_URL + lang + ".json")
    json_data = json.loads(response.content)
    return json_data


def localize(language_data: dict, key: str) -> str:
    """Get the localized name for the specified key.

    Args:
        language_data (dict): The language data, loaded from a JSON file.
        key (str): The key to get the localized name for.

    Returns:
        str: The localized name.
    """
    # Try each of the possible keys in order.
    MAIN_KEY = "CommonMsg/Weapon/WeaponName_Main"
    SUB_KEY = "CommonMsg/Weapon/WeaponName_Sub"
    SPECIAL_KEY = "CommonMsg/Weapon/WeaponName_Special"
    try:
        return language_data[MAIN_KEY][key]
    except KeyError:
        pass
    try:
        return language_data[SUB_KEY][key]
    except KeyError:
        pass
    return language_data[SPECIAL_KEY][key]


@cache
def get_versus_weapons(version: str | None = None) -> list[dict]:
    """Get the versus weapons from the specified version of the datamine. If no
    version is specified, get the latest version.

    Args:
        version (str | None): The version to get the data from. If None, get the
            latest version. Defaults to None.

    Returns:
        list[dict]: The versus weapons.
    """
    weapon_data = get_weapon_data(version=version)
    return [x for x in weapon_data if x.get("Type", None) == "Versus"]


@cache
def get_coop_weapons(version: str | None = None) -> list[dict]:
    """Get the co-op weapons from the specified version of the datamine. If no
    version is specified, get the latest version.

    Args:
        version (str | None): The version to get the data from. If None, get the
            latest version. Defaults to None.

    Returns:
        list[dict]: The co-op weapons.
    """
    weapon_data = get_weapon_data(version=version)
    return [x for x in weapon_data if x.get("Type", None) == "Coop"]


def map_localized_names(
    weapon_data: list[dict[str, str]], lang: str = "USen"
) -> list[dict]:
    """Map the localized names for the specified weapons.

    Args:
        weapon_data (list[dict[str, str]]): The weapon data, loaded from the
            datamine.
        lang (str): The language to use. Defaults to "USen".

    Returns:
        list[dict]: The weapon data with localized names.
    """
    language_data = get_language_data(lang=lang)
    special_regex = re.compile(
        r"(?<=Work\/Gyml\/).*(?=\.spl__WeaponInfoSpecial\.gyml)"
    )
    sub_regex = re.compile(r"(?<=Work\/Gyml\/).*(?=\.spl__WeaponInfoSub\.gyml)")
    for weapon in weapon_data:
        weapon["Name"] = localize(language_data, weapon["__RowId"])
        weapon["Class"] = weapon["__RowId"].split("_")[0]
        special = special_regex.search(weapon["SpecialWeapon"]).group(0)
        sub = sub_regex.search(weapon["SubWeapon"]).group(0)
        weapon["Special"] = localize(language_data, special)
        weapon["Sub"] = localize(language_data, sub)

    return weapon_data


@cache
def get_versus_weapons_simplified(
    version: str | None = None, lang: str = "USen"
) -> WeaponsMap:
    """Get the versus weapons from the specified version of the datamine, but in
    a simplified and localized format. If no version is specified, get the
    latest version. If no language is specified, use English.

    Args:
        version (str | None): The version to get the data from. If None, get the
            latest version. Defaults to None.
        lang (str): The language to use. Defaults to "USen".

    Returns:
        WeaponsMap: The versus weapons.
    """
    full_list = map_localized_names(
        get_versus_weapons(version=version), lang=lang
    )
    out = {}
    for weapon in full_list:
        dic = {
            k: v
            for k, v in weapon.items()
            if k
            in [
                "Name",
                "Special",
                "Sub",
                "Range",
                "SpecialPoint",
                "Class",
            ]
        }
        out[dic["Name"]] = dic
    return out


class WeaponReference:
    def __init__(
        self, version: str | None = None, language: str = "USen"
    ) -> None:
        self._versus_weapons: WeaponsMap | None = None
        self._coop_weapons: WeaponsMap | None = None
        self._version = version
        self._lang = language

    @cached_property
    def versus_weapons(self) -> WeaponsMap:
        if self._versus_weapons is None:
            self._versus_weapons = get_versus_weapons_simplified(
                version=self._version, lang=self._lang
            )
        return self._versus_weapons

    @property
    def versus_weapon_names(self) -> list[str]:
        return [x.lower() for x in self.versus_weapons.keys()]

    @cached_property
    def weapon_classes(self) -> list[str]:
        return set(x["Class"].lower() for x in self.versus_weapons.values())

    def weapon_names_by_class(self, weapon_class: str | list[str]) -> list[str]:
        """Return a list of weapon names for a given weapon class. If given a
        list of classes, return a list of all weapons in those classes. Does not
        separate by class.

        Args:
            weapon_class (str | list[str]): The weapon class to get names for.

        Returns:
            list[str]: A list of weapon names.
        """
        if isinstance(weapon_class, str):
            weapon_class = [weapon_class]
        weapon_class = [x.lower() for x in weapon_class]

        out = []
        for weapon in self.versus_weapons.values():
            if weapon["Class"].lower() in weapon_class:
                out.append(weapon["Name"].lower())
        return out

    def classify_string(self, string: str) -> str:
        """Classify a string as a weapon, ability, or other.

        Args:
            string (str): The string to classify.

        Returns:
            str: The classification.
        """
        string = string.lower()
        if string in self.weapon_classes:
            return "class"
        elif string in self.versus_weapon_names:
            return "weapon"
        else:
            return ""

    def parse_input(
        self, input_: str | list[str]
    ) -> tuple[list[str], list[str]]:
        """Parse a string or list of strings into a list of weapon names.

        Args:
            input_ (str | list[str]): The string or list of strings to parse.

        Raises:
            ValueError: If the input is not recognized

        Returns:
            tuple:
                list[str]: A list of weapon names.
                list[str]: A list of weapon classes.
        """
        if isinstance(input_, str):
            input_ = [input_]
        input_ = [x.lower() for x in input_]

        weapons_list = []
        classes_list = []
        for item in input_:
            classify = self.classify_string(item)
            if classify == "class":
                weapons_list.extend(self.weapon_names_by_class(item))
                classes_list.append(item)
            elif classify == "weapon":
                weapons_list.append(item)
            else:
                raise ValueError(f"Invalid input: {item}")
        return weapons_list, classes_list


class SuperWeaponReference:
    """A class to hold references to all weapon data for all versions of the
    game. If a version is not specified, the latest version is used. If a child
    attribute is called without a version, the latest version is used.
    """

    def __init__(self, preferred_version: str | None = None) -> None:
        self._storage = {}
        self.existing_versions = enumerate_versions()
        if preferred_version is None:
            preferred_version = max(self.existing_versions)
        else:
            preferred_version = self.__parse_version(preferred_version)
        self.preferred_version = preferred_version
        self.create_reference(preferred_version)

    def __parse_version(self, version: str) -> str:
        return version.replace(".", "").replace("v", "")

    def create_reference(self, version: str, language: str = "USen") -> None:
        version = self.__parse_version(version)
        if version not in self._storage:
            self._storage[version] = WeaponReference(version, language)

    def __getitem__(self, version: str) -> WeaponReference:
        version = self.__parse_version(version)
        if version not in self._storage:
            self.create_reference(version)
        return self._storage[version]

    def __getattr__(self, name: str) -> Any:
        """If a child attribute is called without a version, use the preferred
        version. If SuperWeaponReference and WeaponReference both share an
        attribute, the SuperWeaponReference attribute is preferred. This allows
        backwards compatibility without breaking everything.

        Args:
            name (str): The attribute name.

        Raises:
            AttributeError: If the attribute is not found in either class.

        Returns:
            Any: The attribute value.
        """
        if name in self.__dict__:
            return self.__dict__[name]
        # To prevent infinite recursion, check if the attribute exists in the
        # preferred version first.
        weapon_reference = self[self.preferred_version]
        if name in weapon_reference.__dict__ or hasattr(weapon_reference, name):
            return weapon_reference.__getattribute__(name)
        else:
            raise AttributeError(
                "Neither SuperWeaponReference nor WeaponReference have an "
                f"attribute named '{name}'."
            )


WEAPON_MAP = SuperWeaponReference()
