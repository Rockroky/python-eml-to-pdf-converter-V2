# 📧 EML to PDF Converter - Web Edition

> Converti facilmente file EML e PEC in PDF con un'interfaccia web moderna e intuitiva

[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-stable-brightgreen)](https://github.com/Rockroky/python-eml-to-pdf-converter-V2)
[![Flask](https://img.shields.io/badge/flask-2.0%2B-orange)](https://flask.palletsprojects.com/)

![Demo Screenshot](Demo/demo.png)


## ⭐ Caratteristiche Principali

- 🌐 Interfaccia web moderna con drag & drop
- 👁️ Preview in tempo reale del contenuto email
- 🔒 Rilevamento automatico PEC con validazione
- 📎 Gestione completa degli allegati
- 🚀 Server locale auto-configurante
- 📱 Design responsive per tutti i dispositivi
- ✍️ Supporto file firmati (.p7m)
- ⚖️ Conformità normativa per PEC

## 🔧 Architettura Tecnica

### Stack Tecnologico
- Backend: Flask (Python)
- Frontend: JavaScript + HTML5

### Componenti Principali
```
server.py     # Server Flask e API endpoints
v3.py         # Core engine di conversione
index.html    # UI responsive
style.css     # Design system moderno
```

## 📋 Requisiti di Sistema

- Python 3.6 o superiore
- Browser web moderno
- SO: Windows, macOS, Linux

### Dipendenze Python
```bash
flask>=2.0.0
pdfkit>=1.0.0
beautifulsoup4>=4.9.0
```

## 🚀 Installazione

1. Clona il repository:
```bash
git clone https://github.com/Rockroky/python-eml-to-pdf-converter-V2
```

2. Installa le dipendenze:
```bash
pip install flask
pip install reportlab
pip install html2text
```

## 🎯 Guida Rapida

1. Avvia il server:
```bash
python server.py
```

2. Apri il browser all'indirizzo mostrato nel terminale
3. Trascina un file EML nell'area dedicata
4. Visualizza l'anteprima e clicca "Converti"

## 💻 Utilizzo Dettagliato

### API Endpoints

| Endpoint | Metodo | Descrizione |
|----------|---------|-------------|
| /api/parse-eml | POST | Parsing file EML |
| /api/convert-to-pdf | POST | Conversione in PDF |
| /health | GET | Status server |

## ❓ Troubleshooting

- **Server non si avvia**: Verifica porta libera
- **Upload non funziona**: Controlla dimensione file
- **Errori PDF**: Verifica permessi cartella output

## 🛣️ Roadmap

- [ ] Supporto batch conversion
- [ ] Temi PDF personalizzabili
- [ ] API key authentication

## 📄 Licenza

MIT License - Vedi file [LICENSE](LICENSE)

## ⚖️ Note Legali

Questo software è fornito "così com'è". Per l'archiviazione PEC a fini legali, consultare un professionista.
