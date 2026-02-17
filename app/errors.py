from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


def validation_error(details: dict, status_code: int = 422) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": "Validation Failed", "details": details},
    )


def request_validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
    details = {}
    for err in exc.errors():
        loc = err.get("loc", [])
        # loc looks like ("body","priority") or ("query","limit")
        key = ".".join([str(x) for x in loc[1:]]) if len(loc) > 1 else "request"
        details[key] = err.get("msg", "Invalid value")
    return JSONResponse(
        status_code=422,
        content={"error": "Validation Failed", "details": details},
    )


def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    # If we already used our shape, keep it
    if isinstance(exc.detail, dict) and "error" in exc.detail and "details" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    # Fallback shape
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Request Failed", "details": {"message": str(exc.detail)}},
    )
