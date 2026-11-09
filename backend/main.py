from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from datetime import datetime

from predictor import VulnerabilityPredictor


# Initialize
app = FastAPI(title="Smart Contract Vulnerability Detector")
os.makedirs("uploads", exist_ok=True)

# CORS so React can talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://scvds-fyp1.vercel.app"], # We will change this to your Vercel URL later for security
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model once at startup
print("Loading GNN model...")
predictor = VulnerabilityPredictor(model_path="model_files/trained_model.pt")


# In-memory storage (simple, no database)
UPLOADS = {}  # {contract_id: {filename, path, uploaded_at, results}}


@app.get("/")
def home():
    return {
        "message": "Smart Contract Vulnerability Detector API",
        "status": "running",
    }


@app.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    """Upload a .sol file."""
    if not file.filename.endswith(".sol"):
        raise HTTPException(status_code=400, detail="Only .sol files allowed")

    # Save file with unique name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join("uploads", safe_filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Store in memory
    contract_id = timestamp
    UPLOADS[contract_id] = {
        "filename": file.filename,
        "path": file_path,
        "uploaded_at": datetime.now().isoformat(),
        "results": None,
    }

    return {
        "message": "File uploaded",
        "contract_id": contract_id,
        "filename": file.filename,
    }


@app.post("/analyze/{contract_id}")
def analyze_contract(contract_id: str):
    """Run model prediction on an uploaded contract."""
    if contract_id not in UPLOADS:
        raise HTTPException(status_code=404, detail="Contract not found")

    file_path = UPLOADS[contract_id]["path"]

    try:
        results = predictor.predict(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    UPLOADS[contract_id]["results"] = results

    return {
        "contract_id": contract_id,
        "filename": UPLOADS[contract_id]["filename"],
        "total_vulnerabilities": len(results),
        "vulnerabilities": results,
    }


@app.get("/results/{contract_id}")
def get_results(contract_id: str):
    """Get stored analysis results."""
    if contract_id not in UPLOADS:
        raise HTTPException(status_code=404, detail="Contract not found")

    data = UPLOADS[contract_id]
    return {
        "contract_id": contract_id,
        "filename": data["filename"],
        "uploaded_at": data["uploaded_at"],
        "total_vulnerabilities": len(data["results"]) if data["results"] else 0,
        "vulnerabilities": data["results"] or [],
    }


@app.get("/history")
def get_history():
    """List all uploaded contracts and dashboard statistics."""
    contracts = []
    total_vulns = 0
    vulnerable_contracts = 0

    for cid, data in UPLOADS.items():
        # Count total vulnerabilities found across all scans
        if data["results"]:
            total_vulns += len(data["results"])
            if len(data["results"]) > 0:
                vulnerable_contracts += 1

        contracts.append({
            "id": cid,
            "filename": data["filename"],
            "uploaded_at": data["uploaded_at"],
            "analyzed": data["results"] is not None,
            "vuln_count": len(data["results"]) if data["results"] else 0
        })
    
    # Sort newest first
    contracts.sort(key=lambda x: x["uploaded_at"], reverse=True)
    
    return {
        "stats": {
            "total_contracts": len(contracts),
            "vulnerable_contracts": vulnerable_contracts,
            "total_vulnerabilities": total_vulns,
        },
        "contracts": contracts
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)