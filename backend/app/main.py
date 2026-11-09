from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.database import SessionLocal, Contract, Result
from app.detector import detect
import shutil
import os

os.makedirs("uploads", exist_ok=True)
os.makedirs("model_files", exist_ok=True)

app = FastAPI(title="Smart Contract Vulnerability Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Backend running", "status": "ok"}


@app.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    if not file.filename.endswith(".sol"):
        raise HTTPException(status_code=400, detail="Only .sol files")

    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    db = SessionLocal()
    contract = Contract(filename=file.filename, file_path=file_path)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    contract_id = contract.id
    db.close()

    return {
        "message": "Uploaded",
        "contract_id": contract_id,
        "filename": file.filename,
    }


@app.post("/analyze/{contract_id}")
def analyze(contract_id: int):
    db = SessionLocal()
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        db.close()
        raise HTTPException(status_code=404, detail="Not found")

    # Detect vulnerabilities
    vulnerabilities = detect(contract.file_path)

    # Save to database
    for v in vulnerabilities:
        result = Result(
            contract_id=contract_id,
            vulnerability_type=v["type"],
            confidence=v["confidence"],
            severity=v["severity"],
            recommendation=v["recommendation"],
        )
        db.add(result)

    db.commit()
    db.close()

    return {
        "contract_id": contract_id,
        "total_vulnerabilities": len(vulnerabilities),
        "vulnerabilities": vulnerabilities,
    }


@app.get("/results/{contract_id}")
def get_results(contract_id: int):
    db = SessionLocal()
    results = db.query(Result).filter(Result.contract_id == contract_id).all()
    db.close()

    return {
        "contract_id": contract_id,
        "total_vulnerabilities": len(results),
        "vulnerabilities": [
            {
                "vulnerability_type": r.vulnerability_type,
                "confidence_score": r.confidence,
                "severity": r.severity,
                "recommendation": r.recommendation,
            }
            for r in results
        ],
    }


@app.get("/history")
def history():
    db = SessionLocal()
    contracts = db.query(Contract).order_by(Contract.uploaded_at.desc()).all()
    db.close()

    return {
        "contracts": [
            {"id": c.id, "filename": c.filename, "uploaded_at": c.uploaded_at}
            for c in contracts
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
