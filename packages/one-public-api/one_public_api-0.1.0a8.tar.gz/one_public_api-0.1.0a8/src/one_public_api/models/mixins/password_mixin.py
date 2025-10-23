from sqlmodel import Field

from one_public_api.common import constants
from one_public_api.core.i18n import translate as _


class PasswordMixin:
    """
    Mixin class for handling password-related functionality.

    This class provides a structure to include and define user passwords
    with specific constraints. It is designed to store the password attribute
    with validation for the maximum allowed length.

    Attributes
    ----------
    password : str
        Password provided by the user.
    """

    password: str = Field(
        nullable=False,
        max_length=constants.MAX_LENGTH_64,
        description=_("Password provided by the user"),
    )
