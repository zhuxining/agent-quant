import subprocess
import sys

if __name__ == "__main__":
    main_process = subprocess.Popen([
        sys.executable,
        "-m",
        "granian",
        "app.main:app",
        "--interface",
        "asgi",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--loop",
        "uvloop",
        "--reload",
    ])

    openbb_api_process = subprocess.Popen([
        sys.executable,
        "-m",
        "granian",
        "openbb_core.api.rest_api:app",
        "--interface",
        "asgi",
        "--host",
        "0.0.0.0",
        "--port",
        "8001",
        "--loop",
        "uvloop",
        "--reload",
    ])

    openbb_mcp_process = subprocess.Popen([
        sys.executable,
        "-m",
        "openbb_mcp_server.app.app",
        "--host",
        "0.0.0.0",
        "--port",
        "8002",
        "--reload",
    ])

    try:
        main_process.wait()
        openbb_api_process.wait()
        openbb_mcp_process.wait()
    except KeyboardInterrupt:
        main_process.terminate()
        openbb_api_process.terminate()
        openbb_mcp_process.terminate()
        main_process.wait()
        openbb_api_process.wait()
        openbb_mcp_process.wait()
