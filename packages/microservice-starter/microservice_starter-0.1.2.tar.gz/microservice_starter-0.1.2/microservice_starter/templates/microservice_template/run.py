import os
import subprocess

import uvicorn
from dotenv import load_dotenv


def launch_fastapi(env: str, port: int):
    print(f"Using environment: {env}")
    print(f"Loading environment file: .env.{env}")

    if env == "dev":
        # Use Uvicorn directly with live reloading and logging
        print("---------------- DEV MODE ----------------")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            workers=4,
            log_level="info",  # Set log level to display server status
            timeout_keep_alive=120,  # Set timeout to keep the connection alive longer
        )
    elif env == "prod":
        # Use Gunicorn with Uvicorn workers in production
        print("---------------- PROD MODE ----------------")
        command = [
            "gunicorn",
            "-w",
            "6",  # Set the number of workers to 8 for production
            "-k",
            "uvicorn.workers.UvicornWorker",  # Use Uvicorn worker for ASGI
            "-b",
            f"0.0.0.0:{port}",  # Bind to host and port
            "main:app",  # Specify the ASGI app
            "--reload",  # Access log to stdout for visibility
            "--access-logfile",
            "-",  # Access log to stdout for visibility
            "--error-logfile",
            "-",  # Error log to stdout
            "--log-level",
            "info",  # Log level set to info
            "--timeout",
            "1200",  # Worker timeout in seconds
            "--keep-alive",
            "1200",  # Set keep-alive timeout for connections
        ]
        subprocess.run(command)


if __name__ == "__main__":
    env = "prod"

    load_dotenv(f"env/.env.{env}")
    port = int(os.getenv("APP_PORT"))

    # Set the environment you want to run
    launch_fastapi(env=env, port=port)
