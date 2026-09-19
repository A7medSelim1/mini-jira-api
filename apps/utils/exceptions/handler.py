from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Standardized API exception handler.
    Returns consistent JSON structure for error responses:
    {
        "success": false,
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable error message",
            "details": {...}
        }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_code = exc.__class__.__name__
        
        # Standardize validation errors
        if isinstance(response.data, dict):
            details = response.data
            message = "Validation failed." if response.status_code == status.HTTP_400_BAD_REQUEST else str(exc)
        elif isinstance(response.data, list):
            details = {"non_field_errors": response.data}
            message = "Validation failed."
        else:
            details = {"detail": str(response.data)}
            message = str(response.data)

        response.data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "details": details
            }
        }
    else:
        logger.exception("Unhandled server exception: %s", exc)
        response = Response(
            {
                "success": False,
                "error": {
                    "code": "InternalServerError",
                    "message": "An unexpected server error occurred.",
                    "details": {}
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
