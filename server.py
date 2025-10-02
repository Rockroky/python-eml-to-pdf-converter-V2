#!/usr/bin/env python3
"""
Server Flask SEMPLIFICATO per il convertitore EML to PDF
Versione organizzata con HTML e CSS separati
Struttura directory rispettosa dei file esistenti
Avvio automatico su interfaccia di rete locale con browser
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
import os
import tempfile
import uuid
import socket
import webbrowser
import threading
import time
from datetime import datetime

# Importa le funzioni dal tuo script v3.py (nella stessa directory)
try:
    from v3 import parse_eml_file, create_pdf_with_attachments, format_file_size
    print("✅ Modulo v3.py importato correttamente!")
except ImportError as e:
    print(f"❌ ERRORE: Impossibile importare v3.py - {e}")
    print("Assicurati che v3.py sia nella stessa cartella di questo script")
    print(f"Directory corrente: {os.getcwd()}")
    print(f"File nella directory: {os.listdir('.')}")
    exit(1)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # Max 50MB

# CORS manuale senza dipendenze esterne
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Directory paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = tempfile.gettempdir()
UPLOAD_FOLDER = os.path.join(TEMP_DIR, 'eml_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Percorsi per i file statici
HTML_FILE = os.path.join(CURRENT_DIR, 'index.html')
STYLES_DIR = os.path.join(CURRENT_DIR, 'styles')

def get_local_ip():
    """Ottiene l'indirizzo IP locale della macchina"""
    try:
        # Connessione temporanea per ottenere l'IP locale
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # Fallback su localhost se non riesce a determinare l'IP
        return "127.0.0.1"

def open_browser(url, delay=2):
    """Apre il browser dopo un breve delay per permettere al server di avviarsi"""
    def delayed_open():
        time.sleep(delay)
        print(f"🌐 Aprendo il browser su: {url}")
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"⚠️ Impossibile aprire automaticamente il browser: {e}")
            print(f"💡 Apri manualmente il browser su: {url}")
    
    thread = threading.Thread(target=delayed_open, daemon=True)
    thread.start()

@app.route('/')
def index():
    """Serve il file index.html dalla directory corrente"""
    try:
        return send_from_directory(CURRENT_DIR, 'index.html')
    except FileNotFoundError:
        return jsonify({
            'error': 'File index.html non trovato',
            'path': HTML_FILE,
            'suggestion': 'Assicurati che index.html sia nella stessa directory di server.py'
        }), 404

@app.route('/styles/<path:filename>')
def styles(filename):
    """Serve i file CSS dalla cartella styles"""
    try:
        return send_from_directory(STYLES_DIR, filename)
    except FileNotFoundError:
        return jsonify({
            'error': f'File CSS {filename} non trovato',
            'path': os.path.join(STYLES_DIR, filename),
            'suggestion': 'Assicurati che la cartella styles/ contenga i file CSS'
        }), 404

@app.route('/api/parse-eml', methods=['POST'])
def parse_eml():
    """API per analizzare un file EML"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nessun file fornito'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        if not file.filename.lower().endswith('.eml'):
            return jsonify({'error': 'Il file deve essere un .eml'}), 400
        
        # Salva il file temporaneamente
        temp_id = str(uuid.uuid4())
        temp_path = os.path.join(UPLOAD_FOLDER, f"{temp_id}.eml")
        file.save(temp_path)
        
        try:
            # Usa la funzione del tuo script v3.py
            print(f"📧 Analizzando: {temp_path}")
            email_data = parse_eml_file(temp_path)
            print(f"✅ Email analizzata: {email_data['subject']}")
            
            # Aggiungi l'ID temporaneo per riferimento futuro
            email_data['temp_id'] = temp_id
            
            return jsonify(email_data)
            
        except Exception as e:
            print(f"❌ Errore nell'analisi: {e}")
            return jsonify({'error': f'Errore nell\'analisi del file: {str(e)}'}), 500
        finally:
            # Pulisci il file temporaneo in caso di errore
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert-to-pdf', methods=['POST'])
def convert_to_pdf():
    """API per convertire EML in PDF"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nessun file fornito'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        # Salva il file temporaneamente
        temp_id = str(uuid.uuid4())
        eml_path = os.path.join(UPLOAD_FOLDER, f"{temp_id}.eml")
        pdf_path = os.path.join(UPLOAD_FOLDER, f"{temp_id}.pdf")
        
        file.save(eml_path)
        
        try:
            print(f"📧 Convertendo: {eml_path}")
            
            # Usa le funzioni del tuo script v3.py
            email_data = parse_eml_file(eml_path)
            create_pdf_with_attachments(email_data, pdf_path)
            
            print(f"✅ PDF creato: {pdf_path}")
            
            # Invia il PDF come download
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=file.filename.replace('.eml', '.pdf'),
                mimetype='application/pdf'
            )
            
        except Exception as e:
            print(f"❌ Errore nella conversione: {e}")
            return jsonify({'error': f'Errore nella conversione: {str(e)}'}), 500
        finally:
            # Pulisci i file temporanei
            for temp_file in [eml_path, pdf_path]:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
                
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Endpoint per verificare lo stato del server"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.3 - Network Interface + Auto Browser',
        'network': {
            'host': request.host,
            'remote_addr': request.remote_addr,
            'url_root': request.url_root
        },
        'paths': {
            'current_dir': CURRENT_DIR,
            'html_file': HTML_FILE,
            'styles_dir': STYLES_DIR,
            'upload_folder': UPLOAD_FOLDER
        },
        'files_status': {
            'html_exists': os.path.exists(HTML_FILE),
            'styles_dir_exists': os.path.exists(STYLES_DIR),
            'v3_module_exists': os.path.exists(os.path.join(CURRENT_DIR, 'v3.py'))
        }
    })

@app.route('/debug/structure')
def debug_structure():
    """Endpoint di debug per verificare la struttura dei file"""
    structure = {
        'current_directory': CURRENT_DIR,
        'files_in_current_dir': [],
        'styles_directory': STYLES_DIR,
        'files_in_styles_dir': []
    }
    
    # Lista file nella directory corrente
    try:
        structure['files_in_current_dir'] = [
            f for f in os.listdir(CURRENT_DIR) 
            if os.path.isfile(os.path.join(CURRENT_DIR, f))
        ]
    except:
        structure['files_in_current_dir'] = ['Errore nel leggere la directory']
    
    # Lista file nella directory styles
    try:
        if os.path.exists(STYLES_DIR):
            structure['files_in_styles_dir'] = [
                f for f in os.listdir(STYLES_DIR) 
                if os.path.isfile(os.path.join(STYLES_DIR, f))
            ]
        else:
            structure['files_in_styles_dir'] = ['Directory styles non esistente']
    except:
        structure['files_in_styles_dir'] = ['Errore nel leggere la directory styles']
    
    return jsonify(structure)

if __name__ == '__main__':
    print("🚀 Avviando il server Flask con interfaccia di rete...")
    print("📧 Convertitore EML to PDF con apertura browser automatica!")
    print(f"📁 Directory corrente: {CURRENT_DIR}")
    
    # Determina l'IP locale
    local_ip = get_local_ip()
    port = 5000
    
    print(f"🌐 IP locale rilevato: {local_ip}")
    print(f"🔌 Porta: {port}")
    
    # Test delle dipendenze
    try:
        from v3 import parse_eml_file
        print("✅ v3.py importato correttamente!")
    except ImportError as e:
        print(f"❌ ERRORE: {e}")
        print("Assicurati che v3.py sia nella stessa cartella!")
        exit(1)
    
    # Verifica struttura dei file
    print("\n📂 Verifica struttura file:")
    
    if os.path.exists(HTML_FILE):
        print("✅ index.html trovato")
    else:
        print("❌ index.html NON trovato - crealo nella directory principale")
    
    if os.path.exists(STYLES_DIR):
        print("✅ cartella styles/ trovata")
        css_file = os.path.join(STYLES_DIR, 'style.css')
        if os.path.exists(css_file):
            print("✅ style.css trovato")
        else:
            print("❌ style.css NON trovato - crealo in styles/style.css")
    else:
        print("❌ cartella styles/ NON trovata - creala nella directory principale")
        print("💡 Suggerimento: mkdir styles")
    
    # Pulisci i file temporanei all'avvio
    try:
        for file in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("🧹 File temporanei puliti")
    except:
        pass
    
    # URL del server
    server_url = f"http://{local_ip}:{port}"
    
    print("\n" + "="*60)
    print(f"🌐 Server disponibile su:")
    print(f"   📍 Locale:       http://127.0.0.1:{port}")
    print(f"   🌍 Rete locale:  {server_url}")
    print(f"   🔍 Debug:        {server_url}/debug/structure")
    print(f"   ❤️  Health:      {server_url}/health")
    print("="*60)
    print("🚀 Avvio del server in corso...")
    
    # Avvia l'apertura automatica del browser
    open_browser(server_url, delay=1)
    
    # Avvia il server Flask
    try:
        app.run(host=local_ip, port=port, debug=False, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ ERRORE: La porta {port} è già in uso!")
            print(f"💡 Prova a cambiare porta o chiudi l'applicazione che usa la porta {port}")
        else:
            print(f"❌ ERRORE di rete: {e}")
            print(f"💡 Fallback su localhost...")
            server_url = f"http://127.0.0.1:{port}"
            print(f"🌐 Tentativo di avvio su: {server_url}")
            open_browser(server_url, delay=2)
            app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Server fermato dall'utente")
    except Exception as e:
        print(f"❌ Errore imprevisto: {e}")