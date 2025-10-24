import os
from pathlib import Path

from cerberus import Validator as CerberusValidator, errors
from c2d.constants import SUPPORTED_IMAGE_TAGS


# Used with Cerberus to customize error messages.
class CustomErrorHandler(errors.BasicErrorHandler):
    messages = errors.BasicErrorHandler.messages.copy()
    # Mutually Exclusive Fields
    messages[errors.EXCLUDES_FIELD.code] = (
        "Mutually Exclusive: {0} cannot be used together with '{field}'"
    )
    # Empty Lists -> This may need changing if we check for minimum lengths
    # other than lists in future.
    messages[errors.MIN_LENGTH.code] = (
        "Empty: '{field}' must be of type 'list' with minimum length {constraint}"
    )
    messages[errors.DEPENDENCIES_FIELD_VALUE.code] = (
        "'{field}' is only supported with {constraint}"
    )


def get_artefacts_base_images() -> list:
    """Extract framework-simulator combinations from c2d supported tags."""
    images = set()

    for tag in SUPPORTED_IMAGE_TAGS:
        parts = tag.split("-", 2)
        if len(parts) >= 2:
            images.add("-".join(parts[:2]))
    # returns ["framework_version-simulator_version"]
    return list(images)


VALIDATOR = CerberusValidator(error_handler=CustomErrorHandler)
ARTEFACTS_BASE_IMAGES = get_artefacts_base_images()
