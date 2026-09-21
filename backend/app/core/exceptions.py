from fastapi import Request
from fastapi.responses import JSONResponse

class CredentialsException(Exception):
    pass

class NotFoundException(Exception):
    pass

async def credentials_exception_handler(request: Request, exc: CredentialsException):
    return JSONResponse(status_code=401, content={"message": "Could not validate credentials"})

async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(status_code=404, content={"message": "Resource not found"})
