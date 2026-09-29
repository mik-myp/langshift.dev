from fastapi import FastAPI

app = FastAPI(title="H03 Deliberate Failure")


@app.get("/broken")
def broken():
    # Deliberate application bug, not a client validation error.
    raise RuntimeError("deliberate failure for H03")
