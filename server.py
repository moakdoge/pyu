from pathlib import Path
from fastapi import FastAPI, UploadFile, File
import uvicorn
from pyulib import files, metadata, version
if __name__ == "__main__":
    for folder in Path("tests").glob("*"):
        if folder.is_file():
            continue

        metadata.Package.generate_package(folder)
    
    #attempt to find
    print(metadata.packageutils.find_depends("Library3"))
    #uvicorn.run(app, host="127.0.0.1", port=5000)