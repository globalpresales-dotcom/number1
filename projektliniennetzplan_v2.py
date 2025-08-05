import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Projektliniennetzplan (U-Bahn-Stil)", layout="wide")
st.title("🚇 Projektliniennetzplan – Metro-Stil")

st.markdown("Erstelle stilisierte Projektpläne mit parallelen Linien, geteilten Meilensteinen und klaren Strukturen.")

# Beispiel-Daten
st.subheader("📝 Eingabe der Linien und Meilensteine")

example_data = {
    "Linie": ["A", "A", "A", "B", "B", "B"],
    "Farbe": ["blue", "blue", "blue", "green", "green", "green"],
    "Meilenstein": ["Start", "Analyse", "Review", "Start", "Analyse", "Umsetzung"],
    "X": [0, 1, 2, 0, 1, 2],
    "Y": [0, 0, 0, 1, 0, 1],
    "Beschriftung": ["Projektstart", "Anforderungsanalyse", "Abnahmevorbereitung", "Projektstart", "Anforderungsanalyse", "Implementierung"]
}

df = st.data_editor(pd.DataFrame(example_data), num_rows="dynamic", use_container_width=True)

def fig_to_image(fig):
    from io import BytesIO
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return buf

if st.button("🎯 Liniennetz anzeigen"):
    try:
        fig, ax = plt.subplots(figsize=(12, 6))

        # Meilensteine gruppieren
        seen = {}
        for idx, row in df.iterrows():
            key = (row["Meilenstein"], row["X"], row["Y"])
            if key not in seen:
                seen[key] = {"lines": [row["Linie"]], "farbe": [row["Farbe"]], "beschriftung": row["Beschriftung"]}
            else:
                seen[key]["lines"].append(row["Linie"])
                seen[key]["farbe"].append(row["Farbe"])

        # Linien zeichnen
        for linie in df["Linie"].unique():
            linie_df = df[df["Linie"] == linie].sort_values(by=["X", "Y"])
            coords = list(zip(linie_df["X"], linie_df["Y"]))
            farbe = linie_df["Farbe"].iloc[0]
            xs, ys = zip(*coords)
            ax.plot(xs, ys, color=farbe, linewidth=4, label=f"Linie {linie}")

        # Meilensteine zeichnen
        for (ms, x, y), info in seen.items():
            ax.plot(x, y, "o", color="white", markersize=12, markeredgewidth=2, markeredgecolor="black", zorder=5)
            ax.text(x, y + 0.2, ms, ha="center", fontsize=9, fontweight="bold")
            ax.text(x, y - 0.3, info["beschriftung"], ha="center", fontsize=8, style="italic", color="gray")

        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
        ax.set_axis_off()
        ax.legend()
        st.pyplot(fig)

        # Exportoption
        st.download_button("📥 Grafik als PNG exportieren", data=fig_to_image(fig), file_name="netzplan.png", mime="image/png")

    except Exception as e:
        st.error(f"Fehler: {e}")
