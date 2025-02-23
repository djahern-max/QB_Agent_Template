from fastapi import FastAPI, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.services.quickbooks import router as quickbooks_router

app = FastAPI(title="RYZE.ai Agents")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quickbooks_router, prefix="/api/v1", tags=["quickbooks"])


@app.post("/v1/analyze/financial")
async def analyze_financial_document(
    file: UploadFile = File(...), api_key: str = Header(..., convert_underscores=False)
):
    return {"message": "Analysis complete"}


@app.get("/callback")  # Note: not /api/v1/callback
async def quickbooks_callback(code: str, state: str, realmId: str):
    print(f"Received callback with code: {code}")
    print(f"State: {state}")
    print(f"RealmId: {realmId}")

    return {
        "code": code,
        "state": state,
        "realmId": realmId,
        "message": "Authorization successful!",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
