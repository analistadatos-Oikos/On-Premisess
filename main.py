import os
import time
import re
import smtplib
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. CONFIGURACIÓN SEGURA (DESDE GITHUB SECRETS)
# ==========================================
URL_REPORTE = "https://app.powerbi.com/view?r=eyJrIjoiZjU0MmU2ZmYtZjRkYi00YWU5LTg3ZGYtMGNjMGFjYTI2ZTYyIiwidCI6ImZlNzUwYzAwLTUyZWMtNDk5ZS05NjljLTRkNGMzOTAwOTY5ZiIsImMiOjR9"

# AQUÍ ESTÁ LA MAGIA: Leemos las claves secretas de GitHub
USUARIO_GMAIL = os.environ["EMAIL_USER"]
CLAVE_GMAIL = os.environ["EMAIL_PASS"]

DESTINATARIO = "analistadatos@oikos.com.co"
NOMBRE_BOT = "Centinela Oikos BI"
MINUTOS_TOLERANCIA = 55 

# ==========================================
# 2. DISEÑO DEL CORREO (DASHBOARD PRO)
# ==========================================
def armar_html(estado, fecha_pantalla, fecha_actual, antiguedad):
    color_brand = "#002855"     
    color_bg_body = "#f3f4f6"   
    
    if estado == "OK":
        color_status = "#10b981" 
        bg_status_light = "#d1fae5"
        titulo_estado = "SISTEMA OPERATIVO"
        mensaje = "Sincronización exitosa. El Gateway está procesando datos correctamente."
        icono = "✅"
    else:
        color_status = "#ef4444" 
        bg_status_light = "#fee2e2"
        titulo_estado = "FALLA DE SINCRONIZACIÓN"
        mensaje = "No se detectan actualizaciones recientes. Se requiere revisión inmediata del servidor."
        icono = "⛔"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: {color_bg_body}; margin: 0; padding: 0; }}
        .email-wrapper {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
        .header {{ background-color: {color_brand}; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; color: #ffffff; font-size: 18px; letter-spacing: 2px; text-transform: uppercase; font-weight: 700; }}
        .header p {{ color: #a5b4fc; margin: 5px 0 0; font-size: 11px; }}
        .status-bar {{ background-color: {color_status}; height: 6px; width: 100%; }}
        .content {{ padding: 40px 30px; }}
        .status-indicator {{ text-align: center; margin-bottom: 30px; }}
        .status-badge {{ background-color: {bg_status_light}; color: {color_status}; padding: 8px 20px; border-radius: 50px; font-weight: 800; font-size: 14px; display: inline-block; letter-spacing: 0.5px; }}
        .main-message {{ text-align: center; color: #374151; font-size: 16px; line-height: 1.6; margin-bottom: 40px; font-weight: 500; }}
        .data-grid {{ background-color: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb; padding: 20px; }}
        .data-row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #e5e7eb; }}
        .data-row:last-child {{ border-bottom: none; }}
        .label {{ color: #6b7280; font-size: 13px; font-weight: 600; text-transform: uppercase; }}
        .value {{ color: #111827; font-size: 14px; font-weight: 700; text-align: right; }}
        .footer {{ background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 11px; }}
        .footer strong {{ color: {color_brand}; }}
    </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="status-bar"></div>
            <div class="header">
                <h1>OIKOS • Data Intelligence</h1>
                <p>Monitor de Infraestructura On-Premise</p>
            </div>
            <div class="content">
                <div class="status-indicator">
                    <span class="status-badge">{icono} {titulo_estado}</span>
                </div>
                <div class="main-message">{mensaje}</div>
                <div class="data-grid">
                    <div class="data-row">
                        <span class="label">📅 Fecha Reporte (BI)</span>
                        <span class="value">{fecha_pantalla}</span>
                    </div>
                    <div class="data-row">
                        <span class="label">⌚ Hora Servidor</span>
                        <span class="value">{fecha_actual.strftime('%I:%M %p')}</span>
                    </div>
                    <div class="data-row">
                        <span class="label">📉 Desfase Tiempo</span>
                        <span class="value" style="color: {color_status};">{int(antiguedad)} min</span>
                    </div>
                    <div class="data-row">
                        <span class="label">📡 Gateway</span>
                        <span class="value">SRV-OIKOS-MAIN</span>
                    </div>
                </div>
            </div>
            <div class="footer">
                Generado automáticamente por <strong>Centinela Bot v4.0</strong><br>
                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """
    return html

def enviar_correo(estado, fecha_pantalla, fecha_actual, minutos):
    print(f"\n📧 ENVIANDO EMAIL PRO A: {DESTINATARIO}...")
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{NOMBRE_BOT} <{USUARIO_GMAIL}>"
        msg['To'] = DESTINATARIO
        asunto_icono = "🟢" if estado == "OK" else "🔴"
        estado_texto = "Normal" if estado == "OK" else "CRÍTICO"
        msg['Subject'] = f"{asunto_icono} Reporte Gateway: {estado_texto} | {datetime.now().strftime('%I:%M %p')}"
        msg.attach(MIMEText(armar_html(estado, fecha_pantalla, fecha_actual, minutos), 'html'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(USUARIO_GMAIL, CLAVE_GMAIL)
        server.sendmail(USUARIO_GMAIL, DESTINATARIO, msg.as_string())
        server.quit()
        print("✅ ¡CORREO PREMIUM ENVIADO! 👔")
    except Exception as e:
        print(f"\n❌ Error técnico: {e}")

def validar_servicio():
    print("⚙️  Iniciando sistema de vigilancia...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        print("❌ Error de drivers.")
        return

    print(f"🚀 Conectando a Power BI Service...")
    driver.get(URL_REPORTE)
    time.sleep(30) 

    texto = driver.find_element(By.TAG_NAME, "body").text
    match = re.search(r"(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+(?:AM|PM|am|pm))", texto)

    status = "FAIL"
    fecha_encontrada = "No detectada"
    zona_co = pytz.timezone('America/Bogota')
    ahora_real = datetime.now(zona_co).replace(tzinfo=None)
    atraso = 999

    if match:
        fecha_encontrada = match.group(1)
        try:
            dt_reporte = datetime.strptime(fecha_encontrada, "%m/%d/%Y %I:%M:%S %p")
            atraso = (ahora_real - dt_reporte).total_seconds() / 60
            print(f"📉 Desfase: {int(atraso)} min")
            if 0 <= atraso <= MINUTOS_TOLERANCIA:
                status = "OK"
        except:
            pass
    
    driver.quit()
    enviar_correo(status, fecha_encontrada, ahora_real, atraso)

if __name__ == "__main__":
    validar_servicio()
