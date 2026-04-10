# app/core/exceptions.py

from fastapi import HTTPException, status


def bad_request(message: str, errors: list | None = None) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "success": False,
            "message": message,
            "errors": errors or [],
        },
    )


def conflict(message: str, errors: list | None = None) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "success": False,
            "message": message,
            "errors": errors or [],
        },
    )


def unauthorized(message: str, errors: list | None = None) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "message": message,
            "errors": errors or [],
        },
    )


def forbidden(message: str, errors: list | None = None) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "success": False,
            "message": message,
            "errors": errors or [],
        },
    )


def not_found(message: str, errors: list | None = None) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "success": False,
            "message": message,
            "errors": errors or [],
        },
    )