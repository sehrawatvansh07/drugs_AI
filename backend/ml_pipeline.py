import itertools

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from rdkit import Chem
from rdkit.Chem import BRICS, QED
from rdkit.Chem import rdFingerprintGenerator

# Same filename the notebook expects — drop your CSV in the backend/ folder
# next to this file, unrenamed.
DATA_FILE = "DOWNLOAD-gU8RPQ5Wut7KaKJdHzr2fUYYJcpIjb0ClUND2cUakNk_eq_.csv"


# ---------------------------------------------------------------------------
# Cell 2 — Robust data cleaning & deduplication
# ---------------------------------------------------------------------------
def get_col(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower().replace(" ", "") == col.lower().replace(" ", "").replace("_", ""):
                return col
    return None


def canonicalize(smiles):
    try:
        if not isinstance(smiles, str):
            return None
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return Chem.MolToSmiles(mol)
        return None
    except Exception:
        return None


def load_and_clean_data(csv_path: str = DATA_FILE) -> pd.DataFrame:
    df_raw = pd.read_csv(csv_path, sep=";", low_memory=False)

    smiles_col = get_col(df_raw, ["canonicalsmiles", "smiles"])
    rel_col = get_col(df_raw, ["standardrelation", "relation"])
    pchembl_col = get_col(df_raw, ["pchemblvalue", "pIC50"])

    df = df_raw[[smiles_col, rel_col, pchembl_col]].copy()
    df.columns = ["SMILES", "Relation", "pIC50"]

    # Strip whitespace/quotes just in case ChEMBL formatted it weirdly
    df["Relation"] = df["Relation"].astype(str).str.strip().str.replace("'", "").str.replace('"', "")
    df = df[df["Relation"] == "="]

    # Force pIC50 to be numeric before dropping nulls
    df["pIC50"] = pd.to_numeric(df["pIC50"], errors="coerce")
    df = df.dropna(subset=["SMILES", "pIC50"])

    df["SMILES"] = df["SMILES"].apply(canonicalize)
    df = df.dropna(subset=["SMILES"])

    # Deduplicate: if a molecule was tested multiple times, take the median score
    df_clean = df.groupby("SMILES")["pIC50"].median().reset_index()
    return df_clean


# ---------------------------------------------------------------------------
# Cell 6 — Fingerprints (modern MorganGenerator)
# ---------------------------------------------------------------------------
def compute_fingerprints(df_clean: pd.DataFrame):
    fpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

    def smiles_to_fp(smiles):
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return fpgen.GetFingerprintAsNumPy(mol)
        return None

    df_clean = df_clean.copy()
    df_clean["FP"] = df_clean["SMILES"].apply(smiles_to_fp)
    df_clean = df_clean.dropna(subset=["FP"])

    X = np.stack(df_clean["FP"].values)
    y = df_clean["pIC50"].values
    return X, y, fpgen, df_clean


# ---------------------------------------------------------------------------
# Cell 12 — Model architecture
# ---------------------------------------------------------------------------
class DrugPredictor(nn.Module):
    def __init__(self):
        super(DrugPredictor, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(2048, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 1),
        )

    def forward(self, x):
        return self.fc(x)


# ---------------------------------------------------------------------------
# Cells 10 + 12 + 14 — Split, train, evaluate
# ---------------------------------------------------------------------------
def train_model(X: np.ndarray, y: np.ndarray):
    # Phase 5: 70/15/15 split
    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.1764, random_state=42)

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.float32).view(-1, 1)
    X_val_t = torch.tensor(X_val, dtype=torch.float32)
    y_val_t = torch.tensor(y_val, dtype=torch.float32).view(-1, 1)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)
    y_test_t = torch.tensor(y_test, dtype=torch.float32).view(-1, 1)

    train_loader = DataLoader(TensorDataset(X_train_t, y_train_t), batch_size=64, shuffle=True)

    # Phase 6: train
    torch.manual_seed(42)
    model = DrugPredictor()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)

    epochs = 50
    train_losses, val_losses = [], []

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * batch_X.size(0)

        epoch_train_loss = running_loss / len(train_loader.dataset)
        train_losses.append(epoch_train_loss)

        model.eval()
        with torch.no_grad():
            val_preds = model(X_val_t)
            epoch_val_loss = criterion(val_preds, y_val_t).item()
            val_losses.append(epoch_val_loss)

    # Phase 7: evaluate on the held-out test set
    model.eval()
    with torch.no_grad():
        predictions = model(X_test_t).numpy()
        actuals = y_test_t.numpy()

    rmse = float(np.sqrt(mean_squared_error(actuals, predictions)))
    mae = float(mean_absolute_error(actuals, predictions))
    r2 = float(r2_score(actuals, predictions))

    metrics = {"rmse": rmse, "mae": mae, "r2": r2}
    return model, metrics, train_losses, val_losses


# ---------------------------------------------------------------------------
# Cell 16 + 18 — BRICS de novo generation + multi-objective scoring
# ---------------------------------------------------------------------------
def generate_candidates(df_clean: pd.DataFrame, model: nn.Module, fpgen) -> pd.DataFrame:
    # 1. Extract fragments from highly active molecules (same selection as the notebook)
    active_smiles = df_clean[df_clean["pIC50"] > 8.0]["SMILES"].head(50).tolist()
    active_mols = [Chem.MolFromSmiles(s) for s in active_smiles]

    fragments = set()
    for mol in active_mols:
        if mol:
            pieces = BRICS.BRICSDecompose(mol)
            fragments.update(pieces)

    fragment_mols = [Chem.MolFromSmiles(f) for f in fragments]

    # 2. Recombine fragments into new, chemically valid structures
    builder = BRICS.BRICSBuild(fragment_mols)
    generated_candidates = []

    for new_mol in itertools.islice(builder, 500):
        if new_mol:
            try:
                new_mol.UpdatePropertyCache(strict=True)
                Chem.SanitizeMol(new_mol)
                generated_candidates.append(Chem.MolToSmiles(new_mol))
            except Exception:
                continue
        if len(generated_candidates) >= 50:
            break

    generated_candidates = list(set(generated_candidates))

    # 3. Score: Usefulness = (AI Predicted Potency * 0.5) + (RDKit QED * 5.0)
    results = []
    model.eval()
    for s in generated_candidates:
        mol = Chem.MolFromSmiles(s)
        if mol:
            fp = fpgen.GetFingerprintAsNumPy(mol)
            tensor = torch.tensor(fp, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                potency = model(tensor).item()

            qed_score = QED.qed(mol)
            usefulness = (potency * 0.5) + (qed_score * 5.0)

            results.append(
                {
                    "SMILES": s,
                    "Predicted_pIC50": round(float(potency), 3),
                    "QED_DrugLikeness": round(float(qed_score), 3),
                    "Usefulness_Index": round(float(usefulness), 3),
                }
            )

    df_leads = pd.DataFrame(results).sort_values(by="Usefulness_Index", ascending=False).reset_index(drop=True)
    return df_leads
