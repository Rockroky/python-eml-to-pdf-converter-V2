#!/usr/bin/env python3
"""
Script per convertire file EML in PDF aggiungendo automaticamente 
la lista degli allegati alla fine del documento
"""

import email
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import html2text
from datetime import datetime
import re
from email.header import decode_header
from email.utils import parseaddr

def decode_email_header(header_value):
    """Decodifica gli header email che potrebbero essere codificati"""
    if not header_value:
        return ""
    
    try:
        decoded_parts = decode_header(header_value)
        decoded_string = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part
        return decoded_string.strip()
    except:
        return str(header_value).strip()

def extract_email_addresses(header_value):
    """Estrae tutti gli indirizzi email da un header (gestisce più destinatari)"""
    if not header_value:
        return "Non specificato"
    
    decoded_header = decode_email_header(header_value)
    
    # Pulisce e separa gli indirizzi multipli
    addresses = []
    
    # Gestisce diversi separatori comuni
    for separator in [',', ';']:
        if separator in decoded_header:
            parts = decoded_header.split(separator)
            for part in parts:
                part = part.strip()
                if part:
                    name, addr = parseaddr(part)
                    if addr:
                        if name:
                            addresses.append(f"{name} <{addr}>")
                        else:
                            addresses.append(addr)
            break
    else:
        # Un solo indirizzo
        name, addr = parseaddr(decoded_header)
        if addr:
            if name:
                addresses.append(f"{name} <{addr}>")
            else:
                addresses.append(addr)
        else:
            addresses.append(decoded_header)
    
    return "; ".join(addresses) if addresses else "Non specificato"

def format_sender_info(header_value, msg):
    """Formatta le informazioni del mittente includendo il tipo di servizio se presente"""
    if not header_value:
        return "Mittente sconosciuto"
    
    decoded_header = decode_email_header(header_value)
    name, addr = parseaddr(decoded_header)
    
    # Cerca indicatori di posta certificata negli header
    service_type = ""
    
    # Controlla vari header che potrebbero indicare posta certificata
    pec_indicators = [
        'X-Transport', 'X-Trasporto', 'X-TipoRicevuta', 'X-Ricevuta',
        'X-VerificaSicurezza', 'X-Riferimento-Message-ID'
    ]
    
    for header_name in pec_indicators:
        if msg.get(header_name):
            service_type = "Posta Certificata "
            break
    
    # Controlla anche nel dominio dell'email
    if addr and any(keyword in addr.lower() for keyword in ['pec', 'cert', 'certificata', 'legalmail']):
        service_type = "Posta Certificata "
    
    # Controlla nel nome del mittente
    if name and any(keyword in name.lower() for keyword in ['pec', 'certificata', 'cert']):
        if not service_type:  # Solo se non già rilevato
            service_type = "Posta Certificata "
    
    # Formatta il risultato finale
    if addr:
        if name:
            if service_type:
                return f"{service_type}\"{name}\" <{addr}>"
            else:
                return f"\"{name}\" <{addr}>"
        else:
            if service_type:
                return f"{service_type}<{addr}>"
            else:
                return addr
    else:
        if service_type:
            return f"{service_type}{decoded_header}"
        else:
            return decoded_header

def parse_eml_file(eml_path):
    """Legge e analizza il file EML"""
    with open(eml_path, 'rb') as f:
        msg = email.message_from_bytes(f.read())
    
    # Estrae le informazioni principali con gestione migliorata
    subject = decode_email_header(msg.get('Subject', 'Nessun oggetto'))
    
    # Gestione migliorata per mittente con rilevamento tipo servizio
    sender = format_sender_info(msg.get('From'), msg)
    if sender == "Mittente sconosciuto":
        sender = "Mittente sconosciuto"
    
    # Gestione migliorata per destinatari - prende solo il primo valido trovato
    recipient = "Destinatario non specificato"
    
    # Controlla tutti i possibili header per i destinatari (in ordine di priorità)
    for header in ['To', 'to', 'TO']:
        if msg.get(header):
            found_recipient = extract_email_addresses(msg.get(header))
            if found_recipient != "Non specificato":
                recipient = found_recipient
                break
    
    # Se non trova 'To', controlla anche 'Cc' e 'Bcc'
    if recipient == "Destinatario non specificato":
        for header in ['Cc', 'cc', 'CC', 'Bcc', 'bcc', 'BCC']:
            if msg.get(header):
                cc_recipients = extract_email_addresses(msg.get(header))
                if cc_recipients != "Non specificato":
                    recipient = f"CC: {cc_recipients}"
                    break
    
    # Se ancora non trova destinatari, cerca in altri header
    if recipient == "Destinatario non specificato":
        for key, value in msg.items():
            if key.lower() in ['delivered-to', 'x-delivered-to', 'x-original-to']:
                found_recipient = extract_email_addresses(value)
                if found_recipient != "Non specificato":
                    recipient = found_recipient
                    break
    
    # Gestione della data
    date = decode_email_header(msg.get('Date', 'Data sconosciuta'))
    
    # Estrae il corpo del messaggio
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')
                        break
                except:
                    continue
            elif part.get_content_type() == "text/html" and not body:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_body = payload.decode('utf-8', errors='ignore')
                        h = html2text.HTML2Text()
                        h.ignore_links = True
                        body = h.handle(html_body)
                except:
                    continue
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
        except:
            body = str(msg.get_payload())
    
    # Se il corpo è ancora vuoto, prova a estrarlo diversamente
    if not body.strip():
        body = "Contenuto del messaggio non disponibile o vuoto"
    
    # Estrae gli allegati
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            # Controlla sia attachment che inline
            content_disposition = part.get('Content-Disposition', '')
            if 'attachment' in content_disposition or 'inline' in content_disposition:
                filename = part.get_filename()
                if filename:
                    # Decodifica il nome del file
                    filename = decode_email_header(filename)
                    
                    # Calcola la dimensione dell'allegato
                    try:
                        payload = part.get_payload(decode=True)
                        size = len(payload) if payload else 0
                    except:
                        size = 0
                    
                    size_str = format_file_size(size)
                    attachments.append({
                        'filename': filename,
                        'size': size_str,
                        'content_type': part.get_content_type() or 'application/octet-stream'
                    })
    
    return {
        'subject': subject,
        'sender': sender,
        'recipient': recipient,
        'date': date,
        'body': body,
        'attachments': attachments
    }

def format_file_size(size_bytes):
    """Formatta la dimensione del file in formato leggibile"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "kB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    if i == 0:
        return f"{size_bytes} {size_names[i]}"
    else:
        return f"{size_bytes:.1f} {size_names[i]}"

def create_pdf_with_attachments(email_data, output_path):
    """Crea il PDF con il contenuto dell'email e la lista degli allegati"""
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Stile personalizzato per gli allegati
    attachment_style = ParagraphStyle(
        'AttachmentStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        leftIndent=0.5*cm
    )
    
    # Header dell'email
    story.append(Paragraph(f"<b>Oggetto:</b> {email_data['subject']}", styles['Normal']))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"<b>Da:</b> {email_data['sender']}", styles['Normal']))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(f"<b>A:</b> {email_data['recipient']}", styles['Normal']))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(f"<b>Data:</b> {email_data['date']}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Linea separatrice
    story.append(Paragraph("_" * 80, styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Corpo dell'email
    body_lines = email_data['body'].split('\n')
    for line in body_lines:
        line = line.strip()
        if line:
            # Gestisce caratteri speciali per ReportLab
            line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(line, styles['Normal']))
        story.append(Spacer(1, 0.2*cm))
    
    # Se ci sono allegati, aggiungi la sezione allegati
    if email_data['attachments']:
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("_" * 80, styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
        
        # Titolo sezione allegati
        story.append(Paragraph("<b>— Allegati: —</b>", styles['Heading2']))
        story.append(Spacer(1, 0.3*cm))
        
        # Crea tabella degli allegati (solo Nome file e Dimensione)
        attachment_data = [['Nome file', 'Dimensione']]
        
        for attachment in email_data['attachments']:
            attachment_data.append([
                attachment['filename'], 
                attachment['size']
            ])
        
        # Crea la tabella con solo 2 colonne
        attachment_table = Table(attachment_data, colWidths=[12*cm, 3*cm])
        attachment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(attachment_table)
        
        # Aggiunge data e info di consegna
        story.append(Spacer(1, 0.5*cm))
        current_date = datetime.now().strftime("%d/%m/%Y")
        story.append(Paragraph(f"<i>CONSEGNA: Notificazione ai sensi della legge n. 53 del 1994</i>", 
                              attachment_style))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(f"<i>Data: {current_date}</i>", attachment_style))
    
    # Genera il PDF
    doc.build(story)
    print(f"PDF creato: {output_path}")

def convert_eml_to_pdf(eml_file_path, output_pdf_path=None):
    """Funzione principale per convertire EML in PDF"""
    
    if not os.path.exists(eml_file_path):
        print(f"Errore: File {eml_file_path} non trovato")
        return
    
    if output_pdf_path is None:
        output_pdf_path = os.path.splitext(eml_file_path)[0] + '.pdf'
    
    try:
        # Analizza il file EML
        print(f"Analizzando {eml_file_path}...")
        email_data = parse_eml_file(eml_file_path)
        
        # Debug info
        print(f"Oggetto: {email_data['subject']}")
        print(f"Da: {email_data['sender']}")
        print(f"A: {email_data['recipient']}")
        print(f"Data: {email_data['date']}")
        print(f"Trovati {len(email_data['attachments'])} allegati")
        
        for att in email_data['attachments']:
            print(f"  - {att['filename']} ({att['size']})")
        
        # Crea il PDF
        print(f"Creando PDF...")
        create_pdf_with_attachments(email_data, output_pdf_path)
        
        print("Conversione completata!")
        
    except Exception as e:
        print(f"Errore durante la conversione: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Esempio di utilizzo
    eml_file = "esempio.eml"  # Sostituisci con il percorso del tuo file EML
    pdf_file = "output.pdf"   # Sostituisci con il percorso di output desiderato
    
    convert_eml_to_pdf(eml_file, pdf_file)
    
    # Per convertire tutti i file EML in una cartella:
    """
    import glob
    
    eml_files = glob.glob("*.eml")
    for eml_file in eml_files:
        pdf_file = os.path.splitext(eml_file)[0] + ".pdf"
        convert_eml_to_pdf(eml_file, pdf_file)
    """