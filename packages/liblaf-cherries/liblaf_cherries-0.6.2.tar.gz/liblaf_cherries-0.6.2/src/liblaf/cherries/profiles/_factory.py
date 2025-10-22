from typing import Literal

from environs import env

from ._abc import Profile

# ensure profiles are registered
from ._default import ProfileDefault  # noqa: F401
from ._playground import ProfilePlayground  # noqa: F401

type ProfileName = Literal["default", "playground"] | str  # noqa: PYI051
type ProfileLike = ProfileName | Profile | type[Profile]


def factory(profile: ProfileLike | None = None) -> Profile:
    if profile is None and env.bool("DEBUG", False):
        profile = "playground"
    if profile is None:
        profile = env.str("PROFILE", "default")
    if isinstance(profile, str):
        return Profile[profile]()
    if isinstance(profile, Profile):
        return profile
    return profile()
