import logging
from typing import Union

# our own api errors
from ants_platform._utils.request import APIError, APIErrors
from ants_platform.api.core import ApiError

# fern api errors
from ants_platform.api.resources.commons.errors import (
    AccessDeniedError,
    Error,
    MethodNotAllowedError,
    NotFoundError,
    UnauthorizedError,
)
from ants_platform.api.resources.health.errors import ServiceUnavailableError

SUPPORT_URL = "https://ants_platform.com/support"
API_DOCS_URL = "https://api.reference.ants_platform.com"
RBAC_DOCS_URL = "https://ants_platform.com/docs/rbac"
INSTALLATION_DOCS_URL = "https://ants_platform.com/docs/sdk/typescript/guide"
RATE_LIMITS_URL = "https://ants_platform.com/faq/all/api-limits"
PYPI_PACKAGE_URL = "https://pypi.org/project/ants_platform/"

# Error messages
updatePromptResponse = (
    f"Make sure to keep your SDK updated, refer to {PYPI_PACKAGE_URL} for details."
)
defaultServerErrorPrompt = f"This is an unusual occurrence and we are monitoring it closely. For help, please contact support: {SUPPORT_URL}."
defaultErrorResponse = f"Unexpected error occurred. Please check your request and contact support: {SUPPORT_URL}."

# Error response map
errorResponseByCode = {
    500: f"Internal server error occurred. For help, please contact support: {SUPPORT_URL}",
    501: f"Not implemented. Please check your request and contact support for help: {SUPPORT_URL}.",
    502: f"Bad gateway. {defaultServerErrorPrompt}",
    503: f"Service unavailable. {defaultServerErrorPrompt}",
    504: f"Gateway timeout. {defaultServerErrorPrompt}",
    404: f"Internal error occurred. {defaultServerErrorPrompt}",
    400: f"Bad request. Please check your request for any missing or incorrect parameters. Refer to our API docs: {API_DOCS_URL} for details.",
    401: f"Unauthorized. Please check your public/private host settings. Refer to our installation and setup guide: {INSTALLATION_DOCS_URL} for details on SDK configuration.",
    403: f"Forbidden. Please check your access control settings. Refer to our RBAC docs: {RBAC_DOCS_URL} for details.",
    429: f"Rate limit exceeded. For more information on rate limits please see: {RATE_LIMITS_URL}",
}


def generate_error_message_fern(error: Error) -> str:
    if isinstance(error, AccessDeniedError):
        return errorResponseByCode.get(403, defaultErrorResponse)
    elif isinstance(error, MethodNotAllowedError):
        return errorResponseByCode.get(405, defaultErrorResponse)
    elif isinstance(error, NotFoundError):
        return errorResponseByCode.get(404, defaultErrorResponse)
    elif isinstance(error, UnauthorizedError):
        return errorResponseByCode.get(401, defaultErrorResponse)
    elif isinstance(error, ServiceUnavailableError):
        return errorResponseByCode.get(503, defaultErrorResponse)
    elif isinstance(error, ApiError):
        status_code = error.status_code
        return (
            errorResponseByCode.get(status_code, defaultErrorResponse)
            if status_code is not None
            else defaultErrorResponse
        )

    return defaultErrorResponse  # type: ignore


def handle_fern_exception(exception: Error) -> None:
    log = logging.getLogger("ants_platform")
    log.debug(exception)
    error_message = generate_error_message_fern(exception)
    log.error(error_message)


def generate_error_message(exception: Union[APIError, APIErrors, Exception]) -> str:
    if isinstance(exception, APIError):
        status_code = (
            int(exception.status)
            if isinstance(exception.status, str)
            else exception.status
        )
        return f"API error occurred: {errorResponseByCode.get(status_code, defaultErrorResponse)}"
    elif isinstance(exception, APIErrors):
        error_messages = [
            errorResponseByCode.get(
                int(error.status) if isinstance(error.status, str) else error.status,
                defaultErrorResponse,
            )
            for error in exception.errors
        ]
        return "API errors occurred: " + "\n".join(error_messages)
    else:
        return defaultErrorResponse


def handle_exception(exception: Union[APIError, APIErrors, Exception]) -> None:
    log = logging.getLogger("ants_platform")
    log.debug(exception)
    error_message = generate_error_message(exception)
    log.error(error_message)
