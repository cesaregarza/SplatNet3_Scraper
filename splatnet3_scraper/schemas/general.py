from dataclasses import dataclass

from splatnet3_scraper.schemas.base import JSONDataClass


@dataclass(repr=False)
class idSchema(JSONDataClass):
    id: str


@dataclass(repr=False)
class vsModeSchema(JSONDataClass):
    mode: str
    id: str


@dataclass(repr=False)
class vsRuleSchema(JSONDataClass):
    name: str
    id: str
    rule: str = None


@dataclass(repr=False)
class imageSchema(JSONDataClass):
    url: str


@dataclass(repr=False)
class vsStageSchema(JSONDataClass):
    image: imageSchema
    name: str
    id: str


@dataclass(repr=False)
class colorSchema(JSONDataClass):
    r: float
    g: float
    b: float
    a: float

    def to_hex_rgb(self, include_alpha: bool = False) -> str:
        """Converts the color to a hex RGB string.

        Args:
            include_alpha (bool): Whether to include the alpha channel in the
                output. Defaults to False.

        Returns:
            str: The hex RGB string.
        """
        r = round(self.r * 255)
        g = round(self.g * 255)
        b = round(self.b * 255)
        out = f"#{r:02x}{g:02x}{b:02x}"
        if include_alpha:
            a = round(self.a * 255)
            out += f"{a:02x}"
        return out

    # TODO: Fun challenge: Find a way to assign a "nearest" color name to the
    #       color. Not at all necessary and may even make it harder to use,
    #       but it would be cool.


@dataclass(repr=False)
class maskingImageSchema(JSONDataClass):
    height: int
    width: int
    maskImageUrl: str
    overlayImageUrl: str


@dataclass(repr=False)
class specialWeaponSchema(JSONDataClass):
    id: str
    name: str
    image: imageSchema
    maskingImage: maskingImageSchema = None


@dataclass(repr=False)
class subWeaponSchema(JSONDataClass):
    id: str
    name: str
    image: imageSchema


@dataclass(repr=False)
class weaponSchema(JSONDataClass):
    name: str
    image: imageSchema
    specialWeapon: specialWeaponSchema
    id: str
    image3d: imageSchema
    image2d: imageSchema
    image3dThumbnail: imageSchema
    image2dThumbnail: imageSchema
    subWeapon: subWeaponSchema
    originalImage: imageSchema = None

    def get_simple_name(self) -> dict[str, str]:
        """Gets the simple name of the weapon.

        Returns:
            dict[str, str]: A dictionary containing the name of the weapon, the
                name of the special weapon, and the name of the sub weapon.
        """
        return {
            "name": self.name,
            "special": self.specialWeapon.name,
            "sub": self.subWeapon.name,
        }


@dataclass(repr=False)
class badgeSchema(JSONDataClass):
    id: str = None
    image: imageSchema = None


@dataclass(repr=False)
class badgesSchema(JSONDataClass):
    badges: list[badgeSchema]


@dataclass(repr=False)
class backgroundSchema(JSONDataClass):
    textColor: colorSchema
    image: imageSchema
    id: str


@dataclass(repr=False)
class nameplateSchema(JSONDataClass):
    badges: badgesSchema
    background: backgroundSchema

    def get_badges(self) -> list[str]:
        """Gets the list of badges on the nameplate.

        Returns:
            list[str]: A list of the badges on the nameplate.
        """
        return [badge["id"] for badge in self["badges"]]
