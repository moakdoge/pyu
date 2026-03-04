from pathlib import Path
from fastapi import FastAPI, UploadFile, File
import uvicorn
from pyulib import files, metadata

app = FastAPI()

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()   # loads whole file (fine for 1 MiB)
    if not file:
        return 404
    with files.tempfile(file.filename, "wb") as f:
        f.write(data)

    return {"filename": file.filename, "size": len(data)}

@app.get("/add/{a}/{b}")
def add(a: int, b: int):
    return {"result": a + b}

if __name__ == "__main__":
    import time
    pack = metadata.Package("Example Library")
    print(pack.name)
    #uvicorn.run(app, host="127.0.0.1", port=5000)