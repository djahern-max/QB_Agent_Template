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

# Mount the QuickBooks router
app.include_router(quickbooks_router, prefix="/api/v1", tags=["quickbooks"])


@app.post("/v1/analyze/financial")
async def analyze_financial_document(
    file: UploadFile = File(...), api_key: str = Header(..., convert_underscores=False)
):
    return {"message": "Analysis complete"}


# Remove the duplicate callback route since it's now handled in the QuickBooks router

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
