import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Projektliniennetzplan V9", layout="wide")
st.title("🚇 Projektliniennetzplan – V9: Vertikale Darstellung & Zeitleistenoption")

st.markdown("Jetzt mit Umschaltung zwischen horizontaler und vertikaler Darstellung sowie optionaler Zeitleiste.")

st.subheader("⚙️ Einstellungen")

orientation = st.selectbox("Ausrichtung des Plans", ["horizontal", "vertikal"])
show_timeline = st.checkbox("Zeitleiste anzeigen", value=True)

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

if st.button("🎯 Liniennetz anzeigen & exportieren"):
    fig, ax = plt.subplots(figsize=(10, 12) if orientation == "vertikal" else (16, 8))

    text_positions = []
    offsets = {}

    # Linienversatz bei gemeinsamen Haltestellen
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
            ((x0 + x1) * 0.5, y0),
            ((x0 + x1) * 0.5, y1),
            (x1, y1),
        ]
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
        path = Path(verts, codes)
        patch = mpatches.PathPatch(path, facecolor='none', lw=4, edgecolor=color, linestyle=style, zorder=1)
        ax.add_patch(patch)

    # Linien zeichnen
    for linie in df["Linie"].unique():
        ldf = df[df["Linie"] == linie].sort_values(by="Datum")
        for i in range(len(ldf) - 1):
            p0, p1 = ldf.iloc[i], ldf.iloc[i + 1]
            date0, date1 = p0["Datum"], p1["Datum"]
            ms0, ms1 = p0["Meilenstein"], p1["Meilenstein"]
            base0, base1 = p0["Y"], p1["Y"]
            off0 = offsets.get((date0, ms0, linie), 0)
            off1 = offsets.get((date1, ms1, linie), 0)
            style = p0["Linienart"]
            color = p0["Farbe"]

            if orientation == "horizontal":
                x0, x1 = mdates.date2num(date0), mdates.date2num(date1)
                y0, y1 = base0 + off0, base1 + off1
            else:
                y0, y1 = mdates.date2num(date0), mdates.date2num(date1)
                x0, x1 = base0 + off0, base1 + off1

            if (x0 == x1) or (y0 == y1):
                ax.plot([x0, x1], [y0, y1], color=color, lw=4, linestyle=style, zorder=1)
            else:
                draw_curve(x0, y0, x1, y1, color, style)

    # Punkte + Texte
    for idx, row in df.iterrows():
        date = row["Datum"]
        y = row["Y"]
        linie = row["Linie"]
        ms = row["Meilenstein"]
        text = row["Beschriftung"]
        pos = row["Textposition"]
        fsize = row["Schriftgröße"]
        fstyle = row["Schriftart"]
        d = row["Textabstand"]
        offset = offsets.get((date, ms, linie), 0)

        if orientation == "horizontal":
            x = mdates.date2num(date)
            y = y + offset
            px, py = x, y
            text_dx, text_dy = 0, d if pos == "oben" else -d
        else:
            y = mdates.date2num(date)
            x = y + offset
            px, py = x, y
            text_dx, text_dy = d if pos == "rechts" else -d, 0

        ax.plot(px, py, marker="o", color="white", markersize=12,
                markeredgewidth=2.5, markeredgecolor="black", zorder=5)

        tx, ty = px + text_dx, py + text_dy

        while any(abs(ty - yp) < 0.2 and abs((tx - xp)) < 0.5 for xp, yp in text_positions):
            ty += 0.2 if text_dy > 0 else -0.2

        text_positions.append((tx, ty))

        ax.text(tx, ty, text,
                ha="left" if text_dx > 0 else "right" if text_dx < 0 else "center",
                va="center" if orientation == "vertikal" else "bottom" if text_dy > 0 else "top",
                fontsize=fsize,
                fontstyle="italic" if "italic" in fstyle else "normal",
                fontweight="bold" if "bold" in fstyle else "normal",
                zorder=6)

    # Zeitleiste
    if show_timeline:
        timeline_pos = -1.2
        ticks = pd.date_range(start=min_date, end=max_date, freq="3D")
        for tick in ticks:
            val = mdates.date2num(tick)
            if orientation == "horizontal":
                ax.axvline(val, ymin=0, ymax=1, color="lightgray", linestyle="--", linewidth=0.5)
                ax.text(val, timeline_pos - 0.2, tick.strftime('%d.%m'), ha='center', fontsize=8)
            else:
                ax.axhline(val, xmin=0, xmax=1, color="lightgray", linestyle="--", linewidth=0.5)
                ax.text(timeline_pos, val, tick.strftime('%d.%m'), va='center', fontsize=8)

    ax.set_title("Projektliniennetzplan", fontsize=14)
    ax.set_xlim([-2, df["Y"].max() + 1.5] if orientation == "vertikal" else [mdates.date2num(min_date), mdates.date2num(max_date)])
    ax.set_ylim([mdates.date2num(min_date), mdates.date2num(max_date)] if orientation == "vertikal" else [-2, df["Y"].max() + 1.5])
    ax.set_axis_off()
    st.pyplot(fig)

    svg_buf = BytesIO()
    pdf_buf = BytesIO()
    fig.savefig(svg_buf, format="svg", bbox_inches="tight")
    fig.savefig(pdf_buf, format="pdf", bbox_inches="tight")
    svg_buf.seek(0)
    pdf_buf.seek(0)

    st.download_button("⬇️ SVG herunterladen", data=svg_buf, file_name="netzplan_v9.svg", mime="image/svg+xml")
    st.download_button("⬇️ PDF herunterladen", data=pdf_buf, file_name="netzplan_v9.pdf", mime="application/pdf")
