import subprocess
import sys

if __name__ == "__main__":
    main_process = subprocess.Popen(
        [
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
        ]
    )

    try:
        main_process.wait()
    except KeyboardInterrupt:
        main_process.terminate()
        main_process.wait()
