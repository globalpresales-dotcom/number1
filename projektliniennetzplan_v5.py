import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Projektliniennetzplan V5", layout="wide")
st.title("🚇 Projektliniennetzplan – V5: Kurven, Stile & SVG/PDF")

st.markdown("Metro-inspirierte Liniennetzpläne mit geschwungenen Übergängen, Stiloptionen und exportierbarer Vektorgrafik.")

st.subheader("📝 Eingabetabelle")

example_data = {
    "Linie": ["A", "A", "A", "B", "B", "B"],
    "Farbe": ["blue", "blue", "blue", "green", "green", "green"],
    "Meilenstein": ["Start", "Analyse", "Review", "Start", "Analyse", "Umsetzung"],
    "Datum": ["2025-09-01", "2025-09-10", "2025-09-20", "2025-09-01", "2025-09-10", "2025-09-18"],
    "Y": [0, 0, 0, 1, 1, 1],
    "Beschriftung": ["Projektstart", "Analyse", "Review", "Projektstart", "Analyse", "Umsetzung"],
    "Linienart": ["solid", "dashed", "solid", "solid", "dotted", "solid"],
    "Textposition": ["oben", "oben", "oben", "unten", "unten", "unten"]
}

df = st.data_editor(pd.DataFrame(example_data), num_rows="dynamic", use_container_width=True)

try:
    df["Datum"] = pd.to_datetime(df["Datum"])
except Exception as e:
    st.error("❌ Fehler beim Datum. Format: YYYY-MM-DD")
    st.stop()

min_date = df["Datum"].min() - pd.Timedelta(days=2)
max_date = df["Datum"].max() + pd.Timedelta(days=2)

if st.button("🎯 Liniennetz anzeigen & exportieren"):
    fig, ax = plt.subplots(figsize=(14, 6))

    text_positions = []

    def draw_curve(x0, y0, x1, y1, color, style):
        Path = mpath.Path
        dx = (x1 - x0) / np.timedelta64(1, 'D')  # in days
        x0n = mdates.date2num(x0)
        x1n = mdates.date2num(x1)
        verts = [
            (x0n, y0),
            (x0n + (x1n - x0n) * 0.5, y0),
            (x0n + (x1n - x0n) * 0.5, y1),
            (x1n, y1),
        ]
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
        path = Path(verts, codes)
        patch = mpatches.PathPatch(path, facecolor='none', lw=4, edgecolor=color, linestyle=style, zorder=1)
        ax.add_patch(patch)

    # Linien zeichnen
    for linie in df["Linie"].unique():
        ldf = df[df["Linie"] == linie].sort_values(by="Datum")
        for i in range(len(ldf) - 1):
            x0, y0 = ldf.iloc[i]["Datum"], ldf.iloc[i]["Y"]
            x1, y1 = ldf.iloc[i + 1]["Datum"], ldf.iloc[i + 1]["Y"]
            farbe = ldf.iloc[i]["Farbe"]
            stil = ldf.iloc[i]["Linienart"]
            if y0 == y1:
                ax.plot([x0, x1], [y0, y1], color=farbe, lw=4, linestyle=stil, zorder=1)
            else:
                draw_curve(x0, y0, x1, y1, farbe, stil)

    # Haltestellen kombinieren
    seen = {}
    for idx, row in df.iterrows():
        key = (row["Meilenstein"], row["Datum"], row["Y"])
        if key not in seen:
            seen[key] = {"linien": [row["Linie"]], "farbe": row["Farbe"], "beschriftung": row["Beschriftung"], "textpos": row["Textposition"]}
        else:
            seen[key]["linien"].append(row["Linie"])

    # Meilensteine + Texte
    for (ms, datum, y), info in seen.items():
        count = len(set(info["linien"]))
        marker = "s" if count > 1 else "o"
        ax.plot(datum, y, marker=marker, color="white", markersize=16 if count > 1 else 12,
                markeredgewidth=2.5, markeredgecolor="black", zorder=5)

        # Textpositionierung mit einfacher Kollisionsvermeidung
        offset = 0.3 if info["textpos"] == "oben" else -0.4
        y_text = y + offset

        # Prüfe auf bestehende Texte an der Position
        while any(abs(y_text - yp) < 0.15 and abs((mdates.date2num(datum) - mdates.date2num(dp))) < 0.4 for dp, yp in text_positions):
            y_text += 0.15 if offset > 0 else -0.15

        text_positions.append((datum, y_text))

        ax.text(datum, y_text, info["beschriftung"], ha="center", fontsize=9,
                style="italic", fontweight="medium", zorder=6)

    # Format Achsen
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    ax.set_xlim([min_date, max_date])
    ax.set_yticks(sorted(df["Y"].unique()))
    ax.set_yticklabels([f"Linie {l}" for l in df.groupby("Y")["Linie"].first()])
    ax.set_ylim([-1, df["Y"].max() + 1])
    ax.grid(True, axis='x', linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    ax.set_axis_off()
    ax.legend()
    st.pyplot(fig)

    # Exporte
    svg_buf = BytesIO()
    pdf_buf = BytesIO()
    fig.savefig(svg_buf, format="svg", bbox_inches="tight")
    fig.savefig(pdf_buf, format="pdf", bbox_inches="tight")
    svg_buf.seek(0)
    pdf_buf.seek(0)

    st.download_button("⬇️ SVG herunterladen", data=svg_buf, file_name="netzplan.svg", mime="image/svg+xml")
    st.download_button("⬇️ PDF herunterladen", data=pdf_buf, file_name="netzplan.pdf", mime="application/pdf")
