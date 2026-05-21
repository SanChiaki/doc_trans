import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.errors import ConversionDependencyError, ConversionFailedError


class AsposeAdapters:
    def __init__(
        self,
        license_path: Path | None = None,
        word_python: str | None = None,
        cells_python: str | None = None,
        slides_python: str | None = None,
        email_python: str | None = None,
        worker_library_path: Path | None = None,
        worker_timeout_seconds: int = 300,
    ) -> None:
        self.license_path = license_path
        self.word_python = word_python or sys.executable
        self.cells_python = cells_python or sys.executable
        self.slides_python = slides_python or sys.executable
        self.email_python = email_python or sys.executable
        self.worker_library_path = worker_library_path
        self.worker_timeout_seconds = worker_timeout_seconds
        self.project_root = Path(__file__).resolve().parents[2]

    def apply_licenses(self) -> None:
        # Licenses are applied inside the worker process that imports Aspose.
        return

    def convert_word(self, source_path: Path, output_path: Path) -> None:
        self._run_worker(self.word_python, "word", source_path, output_path)

    def convert_excel(self, source_path: Path, output_path: Path) -> None:
        self._run_worker(self.cells_python, "excel", source_path, output_path)

    def convert_presentation(self, source_path: Path, output_path: Path) -> None:
        self._run_worker(self.slides_python, "presentation", source_path, output_path)

    def convert_email(self, source_path: Path, output_path: Path) -> None:
        with TemporaryDirectory() as temp_dir:
            mhtml_path = Path(temp_dir) / "message.mhtml"
            self._run_worker(self.email_python, "email-mhtml", source_path, mhtml_path)
            self._run_worker(self.word_python, "word", mhtml_path, output_path)

    def _run_worker(self, python_executable: str, family: str, source_path: Path, output_path: Path) -> None:
        command = [
            python_executable,
            "-m",
            "app.workers.aspose_convert",
            family,
            str(source_path),
            str(output_path),
        ]
        if self.license_path:
            command.append(str(self.license_path))

        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            str(self.project_root)
            if not existing_pythonpath
            else f"{self.project_root}{os.pathsep}{existing_pythonpath}"
        )
        if self.worker_library_path:
            existing_library_path = env.get("LD_LIBRARY_PATH")
            env["LD_LIBRARY_PATH"] = (
                str(self.worker_library_path)
                if not existing_library_path
                else f"{self.worker_library_path}{os.pathsep}{existing_library_path}"
            )

        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                env=env,
                text=True,
                capture_output=True,
                timeout=self.worker_timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ConversionDependencyError(
                "Configured Aspose worker Python executable was not found.",
                details={"python": python_executable},
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ConversionFailedError(
                "Aspose worker timed out.",
                details={"family": family, "timeout_seconds": self.worker_timeout_seconds},
            ) from exc

        if result.returncode == 2:
            raise ConversionDependencyError(
                self._worker_message(result) or "Missing Aspose dependency.",
                details={"family": family, "stderr": result.stderr.strip()},
            )
        if result.returncode != 0:
            raise ConversionFailedError(
                "Aspose worker failed.",
                details={"family": family, "stderr": result.stderr.strip(), "stdout": result.stdout.strip()},
            )
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ConversionFailedError("Aspose worker did not produce a PDF.", details={"family": family})

    @staticmethod
    def _worker_message(result: subprocess.CompletedProcess) -> str:
        return (result.stderr or result.stdout or "").strip().splitlines()[-1] if (result.stderr or result.stdout) else ""
