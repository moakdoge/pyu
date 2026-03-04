from pathlib import Path
from fastapi import FastAPI, UploadFile, File
import uvicorn
from pyulib import files, metadata, version
if __name__ == "__main__":
    pack = metadata.Package.generate_package(Path("examplelib"))
    #uvicorn.run(app, host="127.0.0.1", port=5000)