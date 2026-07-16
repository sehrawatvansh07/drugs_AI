import io
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from rdkit import Chem
from rdkit.Chem import Draw

from ml_pipeline import (
    DATA_FILE,
    compute_fingerprints,
    generate_candidates,
    load_and_clean_data,
    train_model,
)

STATE: dict = {}


def _serialize_records(df):
    """Make sure every value is a plain Python type before it hits jsonable_encoder."""
    records = df.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if isinstance(v, (np.floating,)):
                r[k] = float(v)
            elif isinstance(v, (np.integer,)):
                r[k] = int(v)
    return records


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"⏳ Loading and cleaning '{DATA_FILE}'...")
    df_clean = load_and_clean_data(DATA_FILE)
    print(f"✅ {len(df_clean)} unique molecules ready.")

    print("⏳ Generating fingerprints...")
    X, y, fpgen, df_clean = compute_fingerprints(df_clean)
    print(f"✅ Feature matrix: {X.shape}")

    print("🚀 Training model (50 epochs)...")
    model, metrics, train_losses, val_losses = train_model(X, y)
    print(f"✅ Model ready — RMSE {metrics['rmse']:.3f} | MAE {metrics['mae']:.3f} | R² {metrics['r2']:.3f}")

    print("🧪 Generating an initial batch of candidates...")
    leads = generate_candidates(df_clean, model, fpgen)
    print(f"✅ {len(leads)} candidates ready.")

    STATE["df_clean"] = df_clean
    STATE["fpgen"] = fpgen
    STATE["model"] = model
    STATE["metrics"] = metrics
    STATE["train_losses"] = train_losses
    STATE["val_losses"] = val_losses
    STATE["leads"] = leads

    yield
    STATE.clear()


app = FastAPI(title="EGFR Inhibitor Discovery API", lifespan=lifespan)

# CORS is only needed if you call the API directly instead of through the
# Vite dev proxy (see frontend/vite.config.js). Left open for local dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
def status():
    m = STATE["metrics"]
    return {
        "ready": True,
        "n_molecules": len(STATE["df_clean"]),
        "rmse": round(m["rmse"], 3),
        "mae": round(m["mae"], 3),
        "r2": round(m["r2"], 3),
    }


@app.get("/api/eda")
def eda():
    df_clean = STATE["df_clean"]
    counts, bin_edges = np.histogram(df_clean["pIC50"], bins=40)
    active = int((df_clean["pIC50"] > 7.0).sum())
    total = len(df_clean)
    return {
        "bins": [float(b) for b in bin_edges[:-1]],
        "counts": [int(c) for c in counts],
        "active_count": active,
        "total": total,
        "active_pct": round(active / total * 100, 1),
    }


@app.get("/api/training-curve")
def training_curve():
    return {
        "train_loss": STATE["train_losses"],
        "val_loss": STATE["val_losses"],
    }


@app.get("/api/candidates")
def candidates(top_n: int = 8):
    df_leads = STATE["leads"]
    return _serialize_records(df_leads.head(top_n))


@app.post("/api/generate")
def generate(top_n: int = 8):
    """Re-runs the BRICS generation + scoring step fresh (cell 16 + 18)."""
    df_leads = generate_candidates(STATE["df_clean"], STATE["model"], STATE["fpgen"])
    STATE["leads"] = df_leads
    return _serialize_records(df_leads.head(top_n))


@app.get("/api/structure")
def structure(smiles: str = Query(...)):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")
    img = Draw.MolToImage(mol, size=(300, 300))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
