from fastapi import FastAPI

app = FastAPI(title="Testing Platform API")

@app.get("/health")
def health_check():
    return {"status": "ok"}