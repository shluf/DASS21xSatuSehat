import os
import numpy as np
import pandas as pd
import pickle
import kagglehub
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# 1. Download dataset terbaru
path = kagglehub.dataset_download("lucasgreenwell/depression-anxiety-stress-scales-responses")
print("Dataset downloaded to:", path)

# 2. Siapkan folder data
files = os.listdir(path)
zip_files = [f for f in files if f.lower().endswith(".zip")]
data_dir = os.path.join(path, "data")
os.makedirs(data_dir, exist_ok=True)

# 3. Ekstrak ZIP jika ada
if zip_files:
    import zipfile
    zip_path = os.path.join(path, zip_files[0])
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(data_dir)
    print("Extracted ZIP →", data_dir)
    files = os.listdir(data_dir)
else:
    data_dir = path

# 4. Temukan CSV
csvs = [f for f in os.listdir(data_dir) if f.lower().endswith(".csv")]
if not csvs:
    raise RuntimeError("Tidak menemukan file .csv di " + data_dir)
print("Found CSV files:", csvs)

# 5. Muat CSV
csv_path = os.path.join(data_dir, csvs[0])
try:
    df = pd.read_csv(csv_path)
except pd.errors.ParserError:
    print("ParserError, retrying with python engine & skip bad lines…")
    df = pd.read_csv(csv_path, sep=None, engine='python', on_bad_lines='skip')

print("Loaded DataFrame shape:", df.shape)

# 6. Ambil hanya jawaban DASS: Q1A…Q21A
answer_cols = [f"Q{i}A" for i in range(1, 22)]
missing = [c for c in answer_cols if c not in df.columns]
if missing:
    raise RuntimeError(f"Kolom jawaban tidak lengkap, hilang: {missing}")

X_items = df[answer_cols].astype(int)

# 7. Hitung skor subskala
# Indeks item 1-based sesuai manual DASS-21
idx_dep    = [3, 5, 10, 13, 16, 17, 21]
idx_anx    = [2, 4, 7, 9, 15, 19, 20]
idx_stress = [1, 6, 8, 11, 12, 14, 18]

s_dep    = X_items.iloc[:, [i-1 for i in idx_dep]].sum(axis=1)
s_anx    = X_items.iloc[:, [i-1 for i in idx_anx]].sum(axis=1)
s_stress = X_items.iloc[:, [i-1 for i in idx_stress]].sum(axis=1)

# 8. Bentuk matriks fitur X
X = pd.concat([s_dep, s_anx, s_stress], axis=1).to_numpy()

# 9. Hitung total skor & mapping severity
# DASS-21: kalikan total dengan 2
total_scores = X.sum(axis=1) * 2

def map_severity(score):
    if score <= 27:
        return "normal"
    elif score <= 42:
        return "mild"
    elif score <= 54:
        return "moderate"
    elif score <= 70:
        return "severe"
    else:
        return "extremely"

y = np.array([map_severity(s) for s in total_scores])

# 10. Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 11. Latih model
clf = RandomForestClassifier(random_state=42)
clf.fit(X_train, y_train)

# 12. Evaluasi
y_pred = clf.predict(X_test)
report = classification_report(y_test, y_pred, zero_division=0)
print("\n=== Classification Report ===")
print(report)

# 13. Simpan model & report
os.makedirs("models", exist_ok=True)
with open("models/dass_classifier.pkl", "wb") as f:
    pickle.dump(clf, f)

pd.DataFrame.from_dict(
    classification_report(y_test, y_pred, output_dict=True, zero_division=0)
).transpose().to_csv("models/classification_report.csv")

print("\nModel tersimpan di: models/dass_classifier.pkl")
print("Report evaluasi di: models/classification_report.csv")
