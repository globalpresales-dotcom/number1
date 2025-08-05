import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Projektliniennetzplan V9.1", layout="wide")
st.title("🚇 Projektliniennetzplan – V9.1: Vertikale Darstellung gefixt")

st.markdown("Diese Version behebt Darstellungsprobleme bei vertikaler Ausrichtung.")

# Einstellungen
orientation = st.selectbox("Ausrichtung des Plans", ["horizontal", "vertikal"])
show_timeline = st.checkbox("Zeitleiste anzeigen", value=True)

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

try:
    df["Datum"] = pd.to_datetime(df["Datum"])
except Exception as e:
    st.error("❌ Fehler beim Datum. Format: YYYY-MM-DD")
    st.stop()

min_date = df["Datum"].min() - pd.Timedelta(days=2)
max_date = df["Datum"].max() + pd.Timedelta(days=2)

# Hauptzeichnung
if st.button("🎯 Liniennetz anzeigen & exportieren"):
    fig, ax = plt.subplots(figsize=(10, 12) if orientation == "vertikal" else (16, 8))

    text_positions = []
    offsets = {}

    # Berechne Offsets für parallele Linien
    shared_points = df.groupby(["Datum", "Meilenstein"]).filter(lambda g: len(g) > 1)
    for (datum, ms), group in shared_points.groupby(["Datum", "Meilenstein"]):
        lines = list(group["Linie"].unique())
        for i, linie in enumerate(lines):
            key = (datum, ms, linie)
            offsets[key] = i * 0.15 - (len(lines) - 1) * 0.15 / 2

    def draw_curve(x0, y0, x1, y1, color, style):
        Path = mpath.Path
        verts = [
            (x0, y0),
            ((x0 + x1) / 2, y0),
            ((x0 + x1) / 2, y1),
            (x1, y1),
        ]
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
        path = Path(verts, codes)
        patch = mpatches.PathPatch(path, facecolor='none', lw=4, edgecolor=color, linestyle=style, zorder=1)
        ax.add_patch(patch)

    # Zeichne Linien
    for linie in df["Linie"].unique():
        ldf = df[df["Linie"] == linie].sort_values(by="Datum")
        for i in range(len(ldf) - 1):
            p0, p1 = ldf.iloc[i], ldf.iloc[i + 1]
            d0, d1 = p0["Datum"], p1["Datum"]
            y0, y1 = p0["Y"], p1["Y"]
            off0 = offsets.get((d0, p0["Meilenstein"], linie), 0)
            off1 = offsets.get((d1, p1["Meilenstein"], linie), 0)
            color = p0["Farbe"]
            style = p0["Linienart"]

            if orientation == "horizontal":
                x0, x1 = mdates.date2num(d0), mdates.date2num(d1)
                y0, y1 = y0 + off0, y1 + off1
            else:
                y0, y1 = mdates.date2num(d0), mdates.date2num(d1)
                x0, x1 = y0 + off0, y1 + off1  # gespiegelt: Datum → y

            if x0 == x1 or y0 == y1:
                ax.plot([x0, x1], [y0, y1], color=color, lw=4, linestyle=style, zorder=1)
            else:
                draw_curve(x0, y0, x1, y1, color, style)

    # Haltestellenpunkte und Texte
    for idx, row in df.iterrows():
        d, y, linie = row["Datum"], row["Y"], row["Linie"]
        ms = row["Meilenstein"]
        text = row["Beschriftung"]
        pos = row["Textposition"]
        fsize = row["Schriftgröße"]
        fstyle = row["Schriftart"]
        d_off = row["Textabstand"]
        offset = offsets.get((d, ms, linie), 0)

        if orientation == "horizontal":
            x = mdates.date2num(d)
            y = y + offset
            tx, ty = x, y + (d_off if pos == "oben" else -d_off)
        else:
            y = mdates.date2num(d)
            x = y + offset
            tx, ty = x + (d_off if pos == "rechts" else -d_off), y

        ax.plot(x, y, marker="o", color="white", markersize=12,
                markeredgewidth=2.5, markeredgecolor="black", zorder=5)

        ax.text(tx, ty, text,
                ha="left" if orientation == "vertikal" and pos == "rechts" else
                   "right" if orientation == "vertikal" and pos == "links" else "center",
                va="bottom" if pos == "oben" else "top" if pos == "unten" else "center",
                fontsize=fsize,
                fontstyle="italic" if "italic" in fstyle else "normal",
                fontweight="bold" if "bold" in fstyle else "normal",
                zorder=6)

    # Zeitleiste (optional)
    if show_timeline:
        ticks = pd.date_range(start=min_date, end=max_date, freq="3D")
        for tick in ticks:
            val = mdates.date2num(tick)
            if orientation == "horizontal":
                ax.axvline(val, ymin=0, ymax=1, color="lightgray", linestyle="--", linewidth=0.5)
                ax.text(val, -1.5, tick.strftime('%d.%m'), ha='center', fontsize=8)
            else:
                ax.axhline(val, xmin=0, xmax=1, color="lightgray", linestyle="--", linewidth=0.5)
                ax.text(-1.5, val, tick.strftime('%d.%m'), va='center', fontsize=8)

    # Achsenbegrenzung
    if orientation == "horizontal":
        ax.set_xlim([mdates.date2num(min_date), mdates.date2num(max_date)])
        ax.set_ylim([-2, df["Y"].max() + 1.5])
    else:
        ax.set_ylim([mdates.date2num(min_date), mdates.date2num(max_date)])
        ax.set_xlim([-2, df["Y"].max() + 1.5])

    ax.set_axis_off()
    st.pyplot(fig)

    # Export
    svg_buf = BytesIO()
    pdf_buf = BytesIO()
    fig.savefig(svg_buf, format="svg", bbox_inches="tight")
    fig.savefig(pdf_buf, format="pdf", bbox_inches="tight")
    svg_buf.seek(0)
    pdf_buf.seek(0)

    st.download_button("⬇️ SVG herunterladen", data=svg_buf, file_name="netzplan_v9_1.svg", mime="image/svg+xml")
    st.download_button("⬇️ PDF herunterladen", data=pdf_buf, file_name="netzplan_v9_1.pdf", mime="application/pdf")
