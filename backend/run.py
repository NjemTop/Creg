import uvicorn
from decouple import config

if __name__ == "__main__":
    uvicorn.run(
        "config.asgi:application",
        host=config("UVICORN_HOST", default="0.0.0.0"),
        port=config("UVICORN_PORT", cast=int, default=8137),
        workers=config("UVICORN_WORKERS", cast=int, default=1),
        log_level=config("UVICORN_LOG_LEVEL", default="info"),
        access_log=config("UVICORN_ACCESS_LOG", cast=bool, default=True),
        timeout_keep_alive=config("UVICORN_TIMEOUT_KEEP_ALIVE", cast=int, default=30),
        proxy_headers=True,
    )
