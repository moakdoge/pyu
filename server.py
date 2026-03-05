from pathlib import Path
import time
from pyulib import files, metadata, version
PARENT = Path(__file__).parent / "tmp"
if PARENT.exists():
    import shutil
    shutil.rmtree(PARENT.absolute())
PARENT.mkdir(exist_ok=True)
if __name__ == "__main__":
    start = time.time()
    for folder in Path("tests").glob("*"):
        if folder.is_file():
            continue

        metadata.Package.generate_package(folder)
    
    #attempt to find

    depends = metadata.packageutils.find_depends("Library3")
    print(depends)
    metadata.packageutils.zip_packages(depends, PARENT)
    print(f"{time.time() - start:.5f}s")
    #uvicorn.run(app, host="127.0.0.1", port=5000)