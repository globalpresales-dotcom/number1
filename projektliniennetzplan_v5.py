import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Projektliniennetzplan V7", layout="wide")
st.title("🚇 Projektliniennetzplan – V7: Punktzentrierung fixiert")

st.markdown("Fix: Haltestellenpunkte (⭘) sind jetzt korrekt zentriert auf versetzten Linien.")

st.subheader("📝 Eingabetabelle")

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
    "Schriftart": ["normal", "italic", "bold", "italic", "normal", "bold"]
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
    fig, ax = plt.subplots(figsize=(16, 8))

    text_positions = []
    y_offsets = {}

    def draw_curve(x0, y0, x1, y1, color, style):
        Path = mpath.Path
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

    # Versatz für parallele Linien
    shared_points = df.groupby(["Datum", "Meilenstein"]).filter(lambda g: len(g) > 1)
    for (datum, ms), group in shared_points.groupby(["Datum", "Meilenstein"]):
        lines = list(group["Linie"].unique())
        for i, linie in enumerate(lines):
            key = (datum, ms, linie)
            y_offsets[key] = i * 0.15 - (len(lines) - 1) * 0.15 / 2  # zentriert

    # Linien zeichnen
    for linie in df["Linie"].unique():
        ldf = df[df["Linie"] == linie].sort_values(by="Datum")
        for i in range(len(ldf) - 1):
            x0, y0_base = ldf.iloc[i]["Datum"], ldf.iloc[i]["Y"]
            x1, y1_base = ldf.iloc[i + 1]["Datum"], ldf.iloc[i + 1]["Y"]
            ms0 = ldf.iloc[i]["Meilenstein"]
            ms1 = ldf.iloc[i + 1]["Meilenstein"]
            o0 = y_offsets.get((x0, ms0, linie), 0)
            o1 = y_offsets.get((x1, ms1, linie), 0)
            y0, y1 = y0_base + o0, y1_base + o1
            farbe = ldf.iloc[i]["Farbe"]
            stil = ldf.iloc[i]["Linienart"]
            if y0 == y1:
                ax.plot([x0, x1], [y0, y1], color=farbe, lw=4, linestyle=stil, zorder=1)
            else:
                draw_curve(x0, y0, x1, y1, farbe, stil)

    # Punkte + Texte
    for idx, row in df.iterrows():
        x = row["Datum"]
        y = row["Y"]
        linie = row["Linie"]
        ms = row["Meilenstein"]
        beschriftung = row["Beschriftung"]
        pos = row["Textposition"]
        font_size = row["Schriftgröße"]
        font_style = row["Schriftart"]
        offset_y = y_offsets.get((x, ms, linie), 0)
        y_draw = y + offset_y

        ax.plot(x, y_draw, marker="o", color="white", markersize=12,
                markeredgewidth=2.5, markeredgecolor="black", zorder=5)

        text_offset = 0.35 if pos == "oben" else -0.45
        y_text = y_draw + text_offset

        while any(abs(y_text - yp) < 0.2 and abs((mdates.date2num(x) - mdates.date2num(xp))) < 0.5 for xp, yp in text_positions):
            y_text += 0.2 if text_offset > 0 else -0.2

        text_positions.append((x, y_text))

        ax.text(x, y_text, beschriftung,
                ha="center", fontsize=font_size,
                fontstyle="italic" if "italic" in font_style else "normal",
                fontweight="bold" if "bold" in font_style else "normal",
                zorder=6)

    # Zeitleiste
    ax.axhline(-1.2, color="gray", lw=1)
    ticks = pd.date_range(start=min_date, end=max_date, freq="3D")
    for tick in ticks:
        ax.axvline(tick, ymin=0, ymax=1, color="lightgray", linestyle="--", linewidth=0.5)
        ax.text(tick, -1.4, tick.strftime('%d.%m'), ha='center', fontsize=8)

    ax.set_xlim([min_date, max_date])
    ax.set_ylim([-2, df["Y"].max() + 1.5])
    ax.set_axis_off()
    ax.set_title("Projektliniennetzplan – zentrierte Punkte bei versetzten Linien", fontsize=14)
    st.pyplot(fig)

    svg_buf = BytesIO()
    pdf_buf = BytesIO()
    fig.savefig(svg_buf, format="svg", bbox_inches="tight")
    fig.savefig(pdf_buf, format="pdf", bbox_inches="tight")
    svg_buf.seek(0)
    pdf_buf.seek(0)

    st.download_button("⬇️ SVG herunterladen", data=svg_buf, file_name="netzplan_v7.svg", mime="image/svg+xml")
    st.download_button("⬇️ PDF herunterladen", data=pdf_buf, file_name="netzplan_v7.pdf", mime="application/pdf")
