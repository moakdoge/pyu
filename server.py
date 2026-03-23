#!/usr/bin/env python3
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

from pyulib.metadata import PackageMetadata, Package
from pyulib import exceptions, files, metadata, other, config
from pyulib.version import PackageVersion

app = FastAPI()


@app.post("/upload")
async def upload_package(file: UploadFile = File(...)):
    if file is None or file.filename is None:
        raise HTTPException(status_code=403, detail="Please provide a file!")
    contents = await file.read()
    if len(contents) > config.MAX_SIZE:
        raise HTTPException(status_code=400, detail=f"File too big ({config.units.num_to_unit(len(contents))}); please keep it beneath {config.units.num_to_unit(config.MAX_SIZE)}!")
    contents = io.BytesIO(contents)
    if not zipfile.is_zipfile(contents):
        raise HTTPException(status_code=400, detail="Invalid zip file")
    contents.seek(0)
    with tempfile.TemporaryDirectory() as m:
        with zipfile.ZipFile(contents, "r") as z:
            size = files.calculate_zip_size(z)
            if size > config.MAX_UNCOMPRESSED_SIZE:
                raise HTTPException(status_code=400, detail=f"Uncompresses to {config.units.num_to_unit(size)} (Max: {config.units.num_to_unit(config.MAX_UNCOMPRESSED_SIZE)})!")
            files.extractall(z, files.vpath(m))
        Package.generate_package(Path(m))

    return 200

@app.get("/packages/list")
async def package_list(amount: int = Query(default=100), offset: int  = Query(default=0)):
    c = metadata.packageutils.load_cache()   

    packs = list(set(_["name"] for _ in c.values()))
    new_dict = []
    for _, p in enumerate(packs[offset:amount]):
        met = PackageMetadata.from_package(p)
        x=met.full_cache.copy()
        new_dict.append(x)

    return JSONResponse(content=new_dict, status_code=200)



@app.get("/packages/{name}/{version}/download")
@app.get("/packages/{name}/download")
async def download(
    name: str,
    depends: bool = True,
    version: str | None = None,
    ):


    package_version: PackageVersion | None = PackageVersion.from_str(version or metadata.packageutils.latest(name))
    result_name=f"{name}.zip"
    met = PackageMetadata.from_package(name, package_version)
    if depends:
        dps = met.depends.copy()
        dps.update({met.name: str(met.version)})
        zip_path, result_name = metadata.packageutils.zip_packages(dps) # type: ignore
        return Response(content=zip_path, media_type="application/zip", headers=other.generate_file_header(result_name))
    else:
        return Response(content=met.path.read_bytes(), media_type="application/zip", headers=other.generate_file_header(result_name))

@app.get("/packages/{name}/{ver}")
@app.get("/packages/{name}")
async def cache(name: str, ver: str | None = None):
    meta = PackageMetadata.from_package(name, PackageVersion.from_str(ver) if ver else None)
    return meta.full_cache

@app.exception_handler(exceptions.BaseHTTPException)
async def handle_pyu_erroappr(request, exc):
    print(str(exc))
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc)}
    )
@app.exception_handler(HTTPException)
async def handle_http(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

if __name__ == "__main__":
    import uvicorn
    metadata.cache()
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")))
