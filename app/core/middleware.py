# app/core/middleware.py
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time
import logging


async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        logging.error(f"Request failed: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
