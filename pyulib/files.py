import os
from pathlib import Path
import tempfile as tmpfle
import zipfile, io, shutil


def tempfile(path: str | Path, *args, **kwargs):
    if isinstance(path, str):
        path = Path(path)
    return tmpfle.NamedTemporaryFile(dir=path, *args, **kwargs)


def zipfolder(folder: Path | str, save_file: Path | None = None) -> bytes:
    if isinstance(folder, str):
        folder = Path(folder)

    if isinstance(save_file, str):
        save_file = Path(save_file)
    if not folder.exists():
        raise FileNotFoundError(f"Folder {folder.absolute()} not found!")

    if save_file:
        with zipfile.ZipFile(save_file, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for f in folder.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(folder))
        return save_file.read_bytes()

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for f in folder.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(folder))

    return buffer.getvalue()
            
def tempfolder():
    return tmpfle.mkdtemp()

class ZipExtractor:
    def __init__(self, file_name: str, file_bytes: bytes | None = None) -> None:
        if file_bytes is None:
            with open(file_name, "rb") as f:
                file_bytes = f.read()
        self._name = file_name
        self._bytes = io.BytesIO(file_bytes)
        self._folder = None 
        self._old_cwd = os.getcwd()
        pass

    def __enter__(self):
        self._folder = tempfolder()
        self._old_cwd = os.getcwd()
        os.chdir(self._folder)
        with zipfile.ZipFile(file=self._bytes) as z:
            z.extractall(path=self._folder)
        return Path(self._folder)

    def __exit__(self, exc_type, exc, tb):
        if self._folder:
            shutil.rmtree(self._folder)
            self._folder = None
        os.chdir(self._old_cwd)
        return False

def extract_zip(path: str | Path | None) -> Path | None:
    if path is None:
        return None