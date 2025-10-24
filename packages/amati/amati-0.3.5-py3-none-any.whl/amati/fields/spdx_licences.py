"""
Validates the idenfitier and licences from the System Package Data
Exchange (SPDX) licence list.
"""

from typing import Any, cast

from amati import AmatiValueError, get
from amati.fields import Str as _Str
from amati.fields.uri import URI

reference_uri = "https://spdx.org/licenses/"

data: list[dict[str, Any]] = cast(list[dict[str, Any]], get("spdx_licences"))

# `seeAlso` is the list of URLs associated with each licence
VALID_LICENCES: dict[str, list[str]] = {
    licence["licenseId"]: licence["seeAlso"] for licence in data
}
VALID_URLS: list[str] = [url for urls in VALID_LICENCES.values() for url in urls]


class SPDXIdentifier(_Str):
    """
    A class representing a valid SPDX license identifier.

    This class validates that a string value is a registered SPDX license identifier
    according to the official SPDX license list. It inherits from _Str to maintain
    compatibility with string operations while adding SPDX-specific validation.

    SPDX identifiers are standardized short-form identifiers for open source licenses,
    such as "MIT", "Apache-2.0", or "GPL-3.0-only".

    Attributes:
        Inherits all attributes from _Str

    Example:
        >>> license_id = SPDXIdentifier("MIT")
        >>> str(license_id)
        'MIT'
        >>> SPDXIdentifier("InvalidLicense")
        Traceback (most recent call last):
        amati.AmatiValueError: message
    """

    def __init__(self, value: str):
        if value not in VALID_LICENCES:
            raise AmatiValueError(
                f"{value} is not a valid SPDX licence identifier", reference_uri
            )


class SPDXURL(URI):
    """
    A class representing a valid SPDX license URL.

    This class validates that a URI is associated with an SPDX license in the official
    SPDX license list. It inherits from URI to maintain compatibility with URI
    validation and operations while adding SPDX-specific validation.

    SPDX license URLs are the official reference URLs for licenses in the SPDX registry,
    typically pointing to the canonical text of the license.

    Attributes:
        Inherits all attributes from URI

    Example:
        >>> license_url = SPDXURL("https://www.apache.org/licenses/LICENSE-2.0")
        >>> license_url.scheme
        'https'
        >>> SPDXURL("https://example.com")
        Traceback (most recent call last):
        amati.AmatiValueError: message
    """

    def __init__(self, value: str):
        super().__init__(value)

        if value not in VALID_URLS:
            raise AmatiValueError(
                f"{value} is not associated with any identifier.", reference_uri
            )
