from __future__ import annotations

import io
import os
import re
import shutil
import time
import tempfile,zipfile
from pathlib import Path


from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from pyulib import files, metadata, other, config
from pyulib.version import PackageVersion

app = FastAPI()


@app.post("/upload")
async def upload_package(file: UploadFile = File(...)):
    if file is None or file.filename is None:
        raise HTTPException(status_code=403, detail="Please provide a file!")
    contents = await file.read()
    if len(contents) > config.MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too big; please keep it beneath 10MiB!")
    contents = io.BytesIO(contents)
    if not zipfile.is_zipfile(contents):
        raise HTTPException(status_code=400, detail="Invalid zip file")
    contents.seek(0)
    with tempfile.TemporaryDirectory() as m:
        with zipfile.ZipFile(contents, "r") as z:
            files.extractall(z, files.vpath(m))
        metadata.Package.generate_package(Path(m))

    return 200

@app.get("/package-list")
def package_list():
    return metadata.packageutils.load_cache()
        
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
    metadata.cache()
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")))