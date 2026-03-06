from __future__ import annotations

import io
import os
import re
import shutil
import time
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from pyulib import files, metadata
from pyulib.version import PackageVersion

app = FastAPI()

TESTS_DIR = Path("tests").resolve()
CACHE_DIR = Path("tmp").resolve()
CACHE_DIR.mkdir(exist_ok=True)

@app.post("/upload")
async def upload_package(file: UploadFile = File(...)):
    if file is None or file.filename is None:
        raise HTTPException(status_code=403, detail="Please provide a file!")
    import zipfile
    contents = await file.read()
    with tempfile.TemporaryDirectory() as m:
        with zipfile.ZipFile(io.BytesIO(contents), "r") as z:
            z.extractall(m)
        metadata.Package.generate_package(Path(m))

    return 200

@app.get("/packages/{name}/download")
def download(
    name: str,
    depends: int = Query(default=0),
    version: str | None = Query(default=None),
    ):
    name = name
    metadata.packageutils.generate_cache()
    pack = metadata.Package(name, version)
    if depends == 1:
        tmpfl = files.tempfolder()
        dps = metadata.packageutils.find_depends(pack.name, pack.version)
        dps.update({pack.name: str(pack.version)})
        zip_path = metadata.packageutils.zip_packages(dps, Path(tmpfl))
        data = zip_path.read_bytes()
        shutil.rmtree(tmpfl)
        return Response(content=data, media_type="application/zip")
        
       # return FileResponse(path=str(zip_path.absolute()), media_type="application/zip", filename=zip_path.name)
    else:
    #pass
        return FileResponse(path=pack._file, media_type="application/zip")



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")))