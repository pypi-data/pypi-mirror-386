"""Module for custom Pydantic validators with user-friendly error messages.

Provides a class with methods to validate various types of input data,
raising PydanticCustomError with predefined error descriptions.
"""

from decimal import Decimal
from typing import Any

from pydantic import EmailStr
from pydantic_core._pydantic_core import PydanticCustomError

from ..error_maps.pydantic import PYDANTIC_ERROR_TYPES

MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0


class PydanticValidator:
    """A class that provides custom validation methods for Pydantic models.

    These methods are designed to raise PydanticCustomError with specific error codes
    and human-readable error messages for better end-user experience.
    """

    error_types = PYDANTIC_ERROR_TYPES

    @classmethod
    def strip_validator(cls, value: str) -> str:
        """Strip whitespace from both ends of a string.

        Args:
            value: Input string to be stripped.

        Returns:
            The stripped string.

        Example:
            ```python
            print(PydanticValidator.strip_validator("  test  "))
            #> "test"
            ```

        """
        return value.strip()

    @classmethod
    def optional_string_validator(cls, value: Any | None) -> str | None:  # noqa: ANN401
        """Validate and strips an optional string value.

        Args:
            value: Input value to be validated.

        Returns:
            A stripped string or None if the value is empty.

        Raises:
            PydanticCustomError: If the value is not a string.

        Example:
            ```python
            print(PydanticValidator.optional_string_validator("  test  "))
            #> "test"

            print(PydanticValidator.optional_string_validator(""))
            #> None

            print(PydanticValidator.optional_string_validator(123))
            #> Traceback (most recent call last):
            #> ...
            #> PydanticCustomError: 'string_type'
            ```

        """
        if value is not None:
            if not isinstance(value, str):
                raise PydanticCustomError("string_type", cls.error_types["string_type"])

            value = cls.strip_validator(value=value)
            if value == "":
                value = None

        return value

    @classmethod
    def email_validator(cls, value: str) -> EmailStr | None:
        """Validate an email address format.

        Args:
            value: Input string to be validated as an email.

        Returns:
            Validated EmailStr object or None if input is invalid.

        Raises:
            PydanticCustomError: If the email format is incorrect.

        Example:
            ```python
            print(PydanticValidator.email_validator("test@example.com"))
            #> EmailStr('test@example.com')

            print(PydanticValidator.email_validator("invalid-email"))
            #> Traceback (most recent call last):
            #> ...
            #> PydanticCustomError: 'incorrect_email'
            ```

        """
        email_str: EmailStr | None = None
        stripped_value: str | None = cls.optional_string_validator(value=value)

        if stripped_value is not None:
            try:
                email_str = EmailStr._validate(stripped_value)  # noqa: SLF001
            except ValueError as exc:
                raise PydanticCustomError(
                    "incorrect_email",
                    cls.error_types["incorrect_email"],
                ) from exc

        return email_str

    @classmethod
    def latitude_validator(cls, value: Decimal) -> Decimal:
        """Validate that a value is a valid geographic latitude.

        Args:
            value: Input Decimal to be validated.

        Returns:
            The validated Decimal value.

        Raises:
            PydanticCustomError: If the value is not in the range [-90.0, 90.0].

        Example:
            ```python
            print(PydanticValidator.latitude_validator(Decimal("45.0")))
            #> Decimal('45.0')

            print(PydanticValidator.latitude_validator(Decimal("100.0")))
            #> Traceback (most recent call last):
            #> ...
            #> PydanticCustomError: 'incorrect_latitude'
            ```

        """
        if not MIN_LATITUDE <= value <= MAX_LATITUDE:
            raise PydanticCustomError(
                "incorrect_latitude",
                cls.error_types["incorrect_latitude"],
            )
        return value

    @classmethod
    def longitude_validator(cls, value: Decimal) -> Decimal:
        """Validate that a value is a valid geographic longitude.

        Args:
            value: Input Decimal to be validated.

        Returns:
            The validated Decimal value.

        Raises:
            PydanticCustomError: If the value is not in the range [-180.0, 180.0].

        Example:
            ```python
            print(PydanticValidator.longitude_validator(Decimal("90.0")))
            #> Decimal('90.0')

            print(PydanticValidator.longitude_validator(Decimal("200.0")))
            #> Traceback (most recent call last):
            #> ...
            #> PydanticCustomError: 'incorrect_longitude'
            ```

        """
        if not MIN_LONGITUDE <= value <= MAX_LONGITUDE:
            raise PydanticCustomError(
                "incorrect_longitude",
                cls.error_types["incorrect_longitude"],
            )
        return value

    @classmethod
    def validate_required_field(cls, value: Any | None) -> Any:  # noqa: ANN401
        """Validate that a field is not missing in update models.

        Args:
            value: Input value to be validated.

        Returns:
            The original value if it's valid.

        Raises:
            PydanticCustomError: If the value is None or empty string.

        Example:
            ```python
            print(PydanticValidator.validate_required_field("test"))
            #> "test"

            print(PydanticValidator.validate_required_field(None))
            #> Traceback (most recent call last):
            #> ...
            #> PydanticCustomError: 'missing'
            ```

        """
        if isinstance(value, str):
            value = cls.optional_string_validator(value=value)

        if value is None:
            raise PydanticCustomError("missing", cls.error_types["missing"])

        return value
