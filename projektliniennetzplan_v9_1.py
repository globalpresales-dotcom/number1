import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.dates as mdates

st.set_page_config(page_title="Projektliniennetzplan V9.5 Diagnose", layout="wide")
st.title("🧪 Projektliniennetzplan – Diagnosemodus V9.5")

st.markdown("Diese Version **zeichnet nichts**, sondern zeigt **jede berechnete Koordinate** und prüft auf `NaN`, `inf`, etc.")

# Beispiel-Daten
example_data = {
    "Linie": ["A", "A", "A", "B", "B", "B"],
    "Farbe": ["blue", "blue", "blue", "green", "green", "green"],
    "Meilenstein": ["Start", "Analyse", "Review", "Start", "Analyse", "Umsetzung"],
    "Datum": ["2025-09-01", "2025-09-10", "2025-09-20", "2025-09-01", "2025-09-10", "2025-09-18"],
    "Y": [0, 0, 0, 1, 1, 1],
    "Beschriftung": ["Projektstart", "Analyse", "Review", "Projektstart", "Analyse", "Umsetzung"],
    "Linienart": ["solid", "dashed", "solid", "solid", "dotted", "solid"],
    "Textposition": ["oben", "oben", "oben", "unten", "unten", "unten"],
    "Schriftgröße": [9, 9, 9, 9, 9, 9],
    "Schriftart": ["normal", "italic", "bold", "italic", "normal", "bold"],
    "Textabstand": [0.35, 0.35, 0.35, 0.35, 0.35, 0.35]
}
df = st.data_editor(pd.DataFrame(example_data), num_rows="dynamic", use_container_width=True)

required_cols = ["Datum", "Linie", "Farbe", "Y", "Beschriftung", "Linienart", "Textposition", "Schriftgröße", "Schriftart", "Textabstand"]
missing = [col for col in required_cols if col not in df.columns]
if missing:
    st.error(f"❌ Fehlende Spalten: {', '.join(missing)}")
    st.stop()

if df[required_cols].isnull().any().any():
    nulls = df[required_cols].isnull().sum()
    st.error("❌ Leere Zellen in Spalten:")
    st.dataframe(nulls[nulls > 0])
    st.stop()

try:
    df["Datum"] = pd.to_datetime(df["Datum"], errors="raise")
except Exception as e:
    st.error(f"❌ Fehler beim Konvertieren der Datum-Spalte: {e}")
    st.stop()

st.subheader("🧾 Simulierte Zeichenanweisungen (ohne Plot)")

offsets = {}
shared_points = df.groupby(["Datum", "Meilenstein"]).filter(lambda g: len(g) > 1)
for (datum, ms), group in shared_points.groupby(["Datum", "Meilenstein"]):
    lines = list(group["Linie"].unique())
    for i, linie in enumerate(lines):
        key = (datum, ms, linie)
        offsets[key] = i * 0.15 - (len(lines) - 1) * 0.15 / 2

for linie in df["Linie"].unique():
    st.markdown(f"### 🚇 Linie: `{linie}`")
    ldf = df[df["Linie"] == linie].sort_values(by="Datum")

    for i in range(len(ldf) - 1):
        p0, p1 = ldf.iloc[i], ldf.iloc[i + 1]
        d0, d1 = p0["Datum"], p1["Datum"]
        y0, y1 = p0["Y"], p1["Y"]
        off0 = offsets.get((d0, p0["Meilenstein"], linie), 0)
        off1 = offsets.get((d1, p1["Meilenstein"], linie), 0)
        style = p0["Linienart"]

        x0 = mdates.date2num(d0)
        x1 = mdates.date2num(d1)
        y0 += off0
        y1 += off1

        msg = f"🔗 Abschnitt {p0['Meilenstein']} → {p1['Meilenstein']}: "
        msg += f"x0={x0:.1f}, y0={y0:.2f} → x1={x1:.1f}, y1={y1:.2f} | Stil: {style}"

        if any(np.isnan(v) or np.isinf(v) for v in [x0, x1, y0, y1]):
            st.error(f"❌ UNGÜLTIGE KOORDINATE: {msg}")
        else:
            st.success(f"✅ {msg}")
