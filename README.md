# drug_AI
Author : Pratyaksh

# EGFR Inhibitor Discovery — Web App


## 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Download ChEMBL CSV into the `backend/` folder 

```

```

Then start the API:

```bash
uvicorn main:app --reload --port 8000
```

The first request to load will take a while — on startup the server runs the
full cleaning → fingerprinting → 50-epoch training pipeline in memory  and caches the trained model and an
initial batch of generated candidates. Watch the terminal for progress logs.
It's ready when you see:

```
✅ Model ready — RMSE ... | MAE ... | R² ...
✅ N candidates ready.
```

## 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`). The dev server
proxies `/api/*` to `http://localhost:8000`, so no CORS setup is needed.

## What's on the page

- **Bioactivity landscape** — the pIC50 histogram from the notebook's EDA cell.
- **Potency vs. drug-likeness** — a live scatter of the current candidate
  batch, with the "ideal zone" (QED > 0.6, pIC50 > 8.0) outlined,as the
  Goldilocks-zone plot .
- **Top generated candidates** — structure images (rendered server-side with
  RDKit, since RDKit doesn't run in the browser) plus potency/QED bars and the
  Usefulness Index. Click **Generate new candidates** to re-run the BRICS
  assembly + scoring step on demand.

## API reference

| Method | Path                       | Returns                                   |
|--------|----------------------------|--------------------------------------------|
| GET    | `/api/status`              | molecule count + test RMSE/MAE/R²          |
| GET    | `/api/eda`                 | pIC50 histogram + active-molecule stats    |
| GET    | `/api/training-curve`      | per-epoch train/val loss                   |
| GET    | `/api/candidates?top_n=8`  | current cached top-N candidates            |
| POST   | `/api/generate?top_n=8`    | re-runs generation, returns new top-N      |
| GET    | `/api/structure?smiles=..` | PNG image of a molecule                    |

## Notes

- Training re-runs on every backend restart (it's fast enough on this dataset
  size that a saved checkpoint wasn't worth the extra moving part — we can add one
  easily in `ml_pipeline.py` if we want to skip retraining).
- `BRICS.BRICSBuild` isn't fully deterministic between process restarts, so a
  fresh `generate` call won't always return the exact same candidates as the
  notebook run — this mirrors the notebook's own behavior if we rerun that
  cell.

