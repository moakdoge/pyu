from __future__ import annotations

import os
import re
import time
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from pyulib import metadata
from pyulib.version import PackageVersion

app = FastAPI()

TESTS_DIR = Path("tests").resolve()
CACHE_DIR = Path("tmp").resolve()
CACHE_DIR.mkdir(exist_ok=True)

_name_re = re.compile(r"^[A-Za-z0-9._-]+$")


def _safe_name(s: str) -> str:
    if not _name_re.match(s):
        raise HTTPException(status_code=400, detail="invalid package name")
    return s


def _ensure_test_packages_built() -> None:
    if not TESTS_DIR.exists():
        raise HTTPException(status_code=500, detail="tests directory missing")
    for folder in TESTS_DIR.glob("*"):
        if folder.is_dir():
            metadata.Package.generate_package(folder)


def _make_bundle_zip(package_name: str) -> Path:
    _ensure_test_packages_built()
    depends = metadata.packageutils.find_depends(package_name)
    if not depends:
        raise HTTPException(status_code=404, detail="package not found")
    CACHE_DIR.mkdir(exist_ok=True)
    out_dir = CACHE_DIR / f"bundle_{package_name}_{int(time.time() * 1000)}"
    out_dir.mkdir(parents=True, exist_ok=True)
    metadata.packageutils.zip_packages(depends, out_dir)
    zips = sorted(out_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not zips:
        raise HTTPException(status_code=500, detail="bundle zip not produced")
    return zips[0]

def _locate_single_zip(name: str, v: str | None) -> Path:
    if v:
        pv = PackageVersion.from_str(v)
        p = metadata.packageutils.locate_package(name, pv)
    else:
        p = metadata.packageutils.locate_package(name, None)

    if not p:
        raise HTTPException(status_code=404, detail="package not found")
    zp = Path(p).resolve()
    if not zp.exists():
        raise HTTPException(status_code=404, detail="package file missing")
    return zp

@app.get("/health")
def health():
    return {"ok": True}

def _bundle_zip(name: str, v: str | None) -> Path:
    if v:
        raise HTTPException(status_code=400, detail="version not supported with depends=1 yet")

    depends = metadata.packageutils.find_depends(name)
    if not depends:
        raise HTTPException(status_code=404, detail="package not found")

    out_dir = CACHE_DIR / f"bundle_{name}_{int(time.time() * 1000)}"
    out_dir.mkdir(parents=True, exist_ok=True)

    metadata.packageutils.zip_packages(depends, out_dir)

    zips = sorted(out_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not zips:
        raise HTTPException(status_code=500, detail="bundle zip not produced")
    return zips[0]


@app.get("/packages/{name}/depends")
def depends(name: str):
    name = _safe_name(name)
    _ensure_test_packages_built()
    d = metadata.packageutils.find_depends(name)
    if not d:
        raise HTTPException(status_code=404, detail="package not found")
    return JSONResponse({"name": name, "depends": sorted(list(d), key=str)})


@app.get("/packages/{name}/download")
def download(
    name: str,
    depends: int = Query(default=1, ge=0, le=1),
    version: str | None = Query(default=None),
):
    name = _safe_name(name)
    _ensure_test_packages_built()

    if depends == 0:
        zip_path = _locate_single_zip(name, version)
        return FileResponse(path=str(zip_path), media_type="application/zip", filename=zip_path.name)

    zip_path = _bundle_zip(name, version)
    return FileResponse(path=str(zip_path), media_type="application/zip", filename=zip_path.name)



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")))