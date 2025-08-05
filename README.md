# 📌 Projektliniennetzplan mit Streamlit

Erstelle interaktive Liniennetzpläne (Netzdiagramme) für Projekte mit Meilensteinen und Abhängigkeiten.

## 🚀 Start

```bash
pip install -r requirements.txt
streamlit run projektplan_app.py
```

## ✨ Features

- Dynamische Eingabe der Meilensteine und Abhängigkeiten
- Visualisierung als gerichteter Graph
- Intuitive Benutzeroberfläche
- Optionales DAG-Layout über `pygraphviz` (`graphviz_layout` mit `dot`); ohne `pygraphviz` wird auf `planar_layout` bzw. `shell_layout` zurückgegriffen
