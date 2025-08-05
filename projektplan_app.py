import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(page_title="Projektliniennetzplan", layout="wide")

st.title("📌 Projektplan als Liniennetzplan (Netzdiagramm)")

st.markdown("""
Dieses Tool erstellt einen Liniennetzplan basierend auf den eingegebenen Meilensteinen und deren Abhängigkeiten.
""")

# Beispiel-Tabelle
example_data = {
    "ID": ["A", "B", "C", "D"],
    "Name": ["Projektstart", "Analyse", "Entwicklung", "Test"],
    "Vorgänger (durch Komma trennen)": ["", "A", "B", "C"]
}

# Eingabe-Tabelle
st.subheader("🔧 Meilenstein-Tabelle eingeben oder anpassen")
df = st.data_editor(pd.DataFrame(example_data), num_rows="dynamic", use_container_width=True)

if st.button("📊 Liniennetzplan erstellen"):
    try:
        # Validierung
        if "ID" not in df.columns or "Name" not in df.columns:
            st.error("Die Tabelle muss die Spalten 'ID' und 'Name' enthalten.")
        else:
            # Graph aufbauen
            G = nx.DiGraph()
            for _, row in df.iterrows():
                ms_id = str(row["ID"]).strip()
                name = str(row["Name"]).strip()
                G.add_node(ms_id, label=name)

            for _, row in df.iterrows():
                ms_id = str(row["ID"]).strip()
                vorgaenger = row.get("Vorgänger (durch Komma trennen)", "")
                if isinstance(vorgaenger, str) and vorgaenger.strip():
                    for v in vorgaenger.split(","):
                        v = v.strip()
                        if v and v in G:
                            G.add_edge(v, ms_id)

            # Layout und Zeichnen
            try:
                from networkx.drawing.nx_agraph import graphviz_layout
                pos = graphviz_layout(G, prog="dot")
            except (ImportError, nx.NetworkXException):
                # Fallback, falls pygraphviz nicht verfügbar oder Layout fehlschlägt
                try:
                    pos = nx.planar_layout(G)
                except (nx.NetworkXException, ValueError):
                    pos = nx.shell_layout(G)

            labels = nx.get_node_attributes(G, 'label')

            fig, ax = plt.subplots(figsize=(10, 7))
            nx.draw(G, pos, with_labels=True, labels=labels, node_color='lightblue',
                    node_size=2000, font_size=10, arrows=True, arrowstyle='->', ax=ax)
            plt.title("Liniennetzplan", fontsize=16)
            st.pyplot(fig)

    except Exception as e:
        st.error(f"Fehler beim Erstellen des Plans: {e}")

st.markdown("---")
st.caption("Entwickelt mit ❤️ und Streamlit – GPT-4")
