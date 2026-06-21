#!/usr/bin/env python3
"""
Bigo.tv SCANNER v15 - Login + Extracción Completa
Hace login para ver: Semillas, Privacidad, y datos ocultos
USO AUTORIZADO SOLAMENTE - Pentesting ético
"""

import requests
import json
import sys
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# PDF
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class BigoLoginScanner:
    def __init__(self, verbose=True, headless=True):
        self.verbose = verbose
        self.base_url = "https://www.bigo.tv"
        self.api_url = "https://ta.bigo.tv/official_website"
        self.user_id = None
        self.driver = None
        self.logged_in = False
        
        # Credenciales (se piden al usuario)
        self.email = None
        self.password = None
        
        # Session para Requests (con cookies de Selenium)
        self.s = requests.Session()
        self.s.timeout = 20
        
        # Configurar Selenium
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)
        
        self.result = {
            "scan_time": datetime.now().isoformat(),
            "user_id": None,
            "logged_in": False,
            "usuario": {
                "id": None,
                "bigo_id": None,
                "nickname": None,
                "avatar": None,
                "avatars": [],
                "nivel": None,
                "genero": None,
                "edad": None,
                "pais": None,
                "ciudad": None,
                "seguidores": None,
                "siguiendo": None,
                "biografia": None,
                "verificado": False,
                "semillas": None,           # info-bean
                "diamantes": None,          # info-diamond
                "monedas": None,            # info-coin
                "sala_actual": None,
                "dispositivo": None,
                "ip": None,
                "email": None,
                "telefono": None,
            },
            "privacidad": {
                "ocultar_prueba_juego": None,
                "ocultar_mascota": None,
                "desactivar_chat_video": None,
                "no_molestar_extraños": None,
                "colapsar_mensajes_extraños": None,
                "no_aceptar_invitaciones_extraños": None,
                "grabacion_momentos_vivo": None,
                "ocultar_ubicacion": None,
                "ocultar_estado_online": None,
                "ocultar_modelo_dispositivo": None,
                "ocultar_tiempo_activo": None,
                "ocultar_estado_familia": None,
                "ocultar_realmatch": None,
            },
            "stream": {
                "activo": False,
                "room_id": None,
                "titulo": None,
                "juego": None,
                "espectadores": None,
                "hls_url": None,
            },
            "enlaces": {}
        }

    def log(self, msg, end="\n", level="INFO"):
        if self.verbose:
            prefix = {
                "INFO": "  ",
                "OK": "  ✓",
                "WARN": "  ⚠️",
                "ERROR": "  ✗",
                "STREAM": "  🔴",
                "USER": "  👤",
                "AGE": "  🎂",
                "GENDER": "  ⚧️",
                "PHOTO": "  📸",
                "PRIVACY": "  🔒",
                "WALLET": "  💰",
                "ROOM": "  🏠",
                "LOGIN": "  🔑",
            }.get(level, "  ")
            print(f"{prefix} {msg}", end=end)

    # ============================================================
    # 1. LOGIN
    # ============================================================
    
    def _login(self):
        """Hace login en Bigo.tv"""
        self.log("\n🔑 Iniciando sesión...", level="LOGIN")
        
        # Pedir credenciales si no se proporcionaron
        if not self.email:
            self.email = input("  Ingrese su email de Bigo: ").strip()
        if not self.password:
            import getpass
            self.password = getpass.getpass("  Ingrese su contraseña: ").strip()
        
        if not self.email or not self.password:
            self.log("Credenciales no proporcionadas", level="ERROR")
            return False
        
        try:
            # Ir a la página de login
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            # Cerrar popup de cookies si aparece
            try:
                accept_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Aceptar') or contains(text(), 'Accept')]")
                accept_btn.click()
                time.sleep(1)
            except:
                pass
            
            # Cambiar a login por email (si es necesario)
            try:
                email_tab = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Email') or contains(text(), 'Correo')]")
                email_tab.click()
                time.sleep(1)
            except:
                pass
            
            # Ingresar email
            email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.clear()
            email_input.send_keys(self.email)
            
            # Ingresar contraseña
            pass_input = self.driver.find_element(By.NAME, "password")
            pass_input.clear()
            pass_input.send_keys(self.password)
            
            # Click en login
            login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Login') or contains(text(), 'Iniciar')]")
            login_btn.click()
            
            # Esperar a que cargue la página
            time.sleep(3)
            
            # Verificar login exitoso
            if "login" not in self.driver.current_url.lower():
                self.logged_in = True
                self.result["logged_in"] = True
                self.log("✅ Login exitoso", level="OK")
                
                # Transferir cookies a Requests
                for cookie in self.driver.get_cookies():
                    self.s.cookies.set(cookie['name'], cookie['value'])
                
                return True
            else:
                self.log("❌ Login fallido", level="ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error en login: {e}", level="ERROR")
            return False

    # ============================================================
    # 2. OBTENER PERFIL COMPLETO (CON LOGIN)
    # ============================================================
    
    def _get_profile_with_login(self, user_id):
        """Obtiene el perfil después de login (incluye semillas)"""
        self.log("\n📄 Obteniendo perfil completo...", level="FIND")
        
        url = f"{self.base_url}/user/{user_id}"
        
        try:
            # Usar Selenium para obtener HTML con login
            self.driver.get(url)
            time.sleep(3)
            
            # Esperar a que cargue
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "nickName")))
            except:
                time.sleep(2)
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # --- PERFIL BÁSICO ---
            nick = soup.find('h1', class_='nickName')
            if nick:
                self.result["usuario"]["nickname"] = nick.text.strip()
                self.log(f"Nickname: {self.result['usuario']['nickname']}", level="OK")
            
            bigo = soup.find('div', class_='bigo-id')
            if bigo:
                match = re.search(r'BIGO\s*ID[:\s]*([^\s]+)', bigo.text, re.I)
                if match:
                    self.result["usuario"]["bigo_id"] = match.group(1)
                    self.log(f"BIGO ID: {self.result['usuario']['bigo_id']}", level="OK")
            
            # Género
            gender = soup.find('div', class_='gender')
            if gender:
                if 'woman' in gender.get('class', []):
                    self.result["usuario"]["genero"] = "Femenino"
                    self.log("Género: Femenino", level="GENDER")
                elif 'man' in gender.get('class', []):
                    self.result["usuario"]["genero"] = "Masculino"
                    self.log("Género: Masculino", level="GENDER")
            
            # Edad
            age = soup.find('span', class_='gender-num')
            if age and age.text.strip().isdigit():
                self.result["usuario"]["edad"] = age.text.strip()
                self.log(f"Edad: {self.result['usuario']['edad']} años", level="AGE")
            
            # --- SEMILLAS / WALLET (info-bean) ---
            bean = soup.find('div', class_='info-bean')
            if bean and bean.text.strip().isdigit():
                self.result["usuario"]["semillas"] = int(bean.text.strip())
                self.log(f"💰 Semillas: {self.result['usuario']['semillas']:,}", level="WALLET")
            else:
                # Buscar con regex
                bean_match = re.search(r'info-bean["\']>([\d,]+)</div>', html)
                if bean_match:
                    bean_val = int(re.sub(r'[,]', '', bean_match.group(1)))
                    self.result["usuario"]["semillas"] = bean_val
                    self.log(f"💰 Semillas (regex): {bean_val:,}", level="WALLET")
            
            # --- DIAMANTES (info-diamond) ---
            diamond = soup.find('div', class_='info-diamond')
            if diamond and diamond.text.strip().isdigit():
                self.result["usuario"]["diamantes"] = int(diamond.text.strip())
                self.log(f"💎 Diamantes: {self.result['usuario']['diamantes']:,}", level="WALLET")
            
            # --- MONEDAS (info-coin) ---
            coin = soup.find('div', class_='info-coin')
            if coin and coin.text.strip().isdigit():
                self.result["usuario"]["monedas"] = int(coin.text.strip())
                self.log(f"🪙 Monedas: {self.result['usuario']['monedas']:,}", level="WALLET")
            
            # --- AVATARS ---
            avatars = []
            preview = soup.find('div', class_='img-preview')
            if preview:
                for img in preview.find_all('img'):
                    src = img.get('src', '')
                    if src and 'bigo.sg' in src:
                        avatars.append(src)
            
            if not avatars:
                og = soup.find('meta', property='og:image')
                if og and og.get('content'):
                    avatars.append(og['content'])
            
            self.result["usuario"]["avatars"] = avatars
            if avatars:
                self.result["usuario"]["avatar"] = avatars[0]
                self.log(f"✅ {len(avatars)} fotos encontradas", level="OK")
            
            # --- PAÍS ---
            flag = re.search(r'([🇦-🇿]{2,})', html)
            if flag:
                flag_map = {'🇱🇾': 'LY', '🇺🇸': 'US', '🇲🇽': 'MX', '🇦🇷': 'AR',
                           '🇧🇷': 'BR', '🇨🇴': 'CO', '🇵🇪': 'PE', '🇨🇱': 'CL',
                           '🇪🇸': 'ES', '🇫🇷': 'FR', '🇩🇪': 'DE', '🇮🇹': 'IT',
                           '🇵🇹': 'PT', '🇬🇧': 'GB', '🇹🇷': 'TR', '🇷🇺': 'RU',
                           '🇯🇵': 'JP', '🇰🇷': 'KR', '🇨🇳': 'CN', '🇮🇳': 'IN',
                           '🇮🇩': 'ID', '🇹🇭': 'TH', '🇻🇳': 'VN', '🇵🇭': 'PH',
                           '🇲🇾': 'MY', '🇸🇬': 'SG'}
                if flag.group(1) in flag_map:
                    self.result["usuario"]["pais"] = flag_map[flag.group(1)]
                    self.log(f"País: {flag_map[flag.group(1)]}", level="LOCATION")
            
            # --- SALA ACTUAL ---
            title = soup.find('title')
            if title:
                sala = title.text
                sala = re.sub(r'\s*[|│]\s*BIGO\s*LIVE.*$', '', sala)
                sala = re.sub(r'Watch\s+', '', sala)
                sala = re.sub(r'Live Stream on.*$', '', sala)
                if sala.strip():
                    self.result["usuario"]["sala_actual"] = sala.strip()
                    self.log(f"🏠 Sala: {sala.strip()[:50]}", level="ROOM")
            
            # --- BIOGRAFÍA ---
            meta = soup.find('meta', attrs={'name': 'description'})
            if meta and meta.get('content'):
                self.result["usuario"]["biografia"] = meta['content'][:200]
            
            # --- SEGUIDORES ---
            followers = soup.find('span', class_='followers-num')
            if followers:
                try:
                    self.result["usuario"]["seguidores"] = int(re.sub(r'[,\.]', '', followers.text.strip()))
                except:
                    pass
            
            self.log("✅ Perfil obtenido correctamente", level="OK")
            return True
            
        except Exception as e:
            self.log(f"Error: {e}", level="ERROR")
            return False

    # ============================================================
    # 3. PRIVACIDAD (después de login)
    # ============================================================
    
    def _get_privacy_settings(self):
        """Obtiene configuración de privacidad"""
        self.log("\n🔒 Obteniendo configuración de privacidad...", level="PRIVACY")
        
        try:
            # Ir a configuración
            self.driver.get(f"{self.base_url}/userCenter/setting")
            time.sleep(3)
            
            # Buscar sección de privacidad
            try:
                privacy_tab = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Privacidad') or contains(text(), 'Privacy')]")
                privacy_tab.click()
                time.sleep(2)
            except:
                pass
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar switches de privacidad
            switches = soup.find_all(['div', 'span', 'label'], class_=re.compile(r'(switch|toggle|privacy|setting|item)'))
            
            privacy_data = {}
            for switch in switches:
                text = switch.text.strip()
                if text and len(text) > 3:
                    # Detectar estado
                    is_active = 'active' in switch.get('class', []) or 'on' in switch.get('class', [])
                    is_checked = switch.find('input', {'checked': True}) is not None
                    is_enabled = is_active or is_checked
                    
                    # Mapear
                    key = self._map_privacy_text(text)
                    if key:
                        privacy_data[key] = is_enabled
            
            # Aplicar
            if privacy_data:
                self._apply_privacy(privacy_data)
                self.log(f"✅ {len(privacy_data)} opciones obtenidas", level="OK")
                return True
            
            # Fallback: buscar en HTML
            self._extract_privacy_from_html(html)
            return True
            
        except Exception as e:
            self.log(f"Error en privacidad: {e}", level="WARN")
            return False
    
    def _map_privacy_text(self, text):
        text_lower = text.lower()
        mapping = {
            'prueba de juego': 'ocultar_prueba_juego',
            'juego de prueba': 'ocultar_prueba_juego',
            'mascota': 'ocultar_mascota',
            'chat de video': 'desactivar_chat_video',
            'video con amigos': 'desactivar_chat_video',
            'no molestar': 'no_molestar_extraños',
            'molestar a extraños': 'no_molestar_extraños',
            'mensajes extraños': 'colapsar_mensajes_extraños',
            'mensaje extraño': 'colapsar_mensajes_extraños',
            'invitaciones': 'no_aceptar_invitaciones_extraños',
            'invitación': 'no_aceptar_invitaciones_extraños',
            'grabación de momentos': 'grabacion_momentos_vivo',
            'momentos en vivo': 'grabacion_momentos_vivo',
            'ubicación': 'ocultar_ubicacion',
            'estado en línea': 'ocultar_estado_online',
            'modelo de dispositivo': 'ocultar_modelo_dispositivo',
            'tiempo activo': 'ocultar_tiempo_activo',
            'familia': 'ocultar_estado_familia',
            'realmatch': 'ocultar_realmatch',
        }
        for key, value in mapping.items():
            if key in text_lower:
                return value
        return None
    
    def _extract_privacy_from_html(self, html):
        patterns = {
            'ocultar_prueba_juego': ['prueba de juego', 'juego de prueba'],
            'ocultar_mascota': ['mascota'],
            'desactivar_chat_video': ['chat de video', 'video con amigos'],
            'no_molestar_extraños': ['no molestar', 'molestar a extraños'],
            'colapsar_mensajes_extraños': ['mensajes extraños', 'mensaje extraño'],
            'no_aceptar_invitaciones_extraños': ['invitaciones', 'invitación'],
            'grabacion_momentos_vivo': ['grabación de momentos', 'momentos en vivo'],
            'ocultar_ubicacion': ['ubicación'],
            'ocultar_estado_online': ['estado en línea'],
            'ocultar_modelo_dispositivo': ['modelo de dispositivo'],
            'ocultar_tiempo_activo': ['tiempo activo'],
            'ocultar_estado_familia': ['miembros de la familia', 'familia'],
            'ocultar_realmatch': ['realmatch'],
        }
        
        for key, terms in patterns.items():
            for term in terms:
                if term.lower() in html.lower():
                    if re.search(rf'.{{0,200}}{term}.{{0,200}}(?:active|on|checked|true)', html, re.I):
                        self.result["privacidad"][key] = True
                        self.log(f"🔒 {term}: Activado", level="PRIVACY")
                    elif re.search(rf'.{{0,200}}{term}.{{0,200}}(?:off|false|inactive)', html, re.I):
                        self.result["privacidad"][key] = False
                        self.log(f"🔒 {term}: Desactivado", level="PRIVACY")
                    break
    
    def _apply_privacy(self, data):
        for key, value in data.items():
            if key in self.result["privacidad"]:
                self.result["privacidad"][key] = value
                status = "Activado" if value else "Desactivado"
                self.log(f"🔒 {key.replace('_', ' ').title()}: {status}", level="PRIVACY")

    # ============================================================
    # 4. STUDIO INFO
    # ============================================================
    
    def _get_studio_info(self, user_id):
        self.log("\n🎥 getInternalStudioInfo (POST)", level="STREAM")
        url = f"{self.api_url}/studio/getInternalStudioInfo"
        
        if not user_id.isdigit():
            url_html = f"{self.base_url}/user/{user_id}"
            try:
                resp = self.s.get(url_html)
                if resp.status_code == 200:
                    site_match = re.search(r'"siteId"\s*[:]\s*"(\d+)"', resp.text)
                    if site_match:
                        user_id = site_match.group(1)
                    else:
                        return
            except:
                return
        
        try:
            resp = self.s.post(url, data={"siteId": user_id})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 and data.get("data"):
                    d = data["data"]
                    self.result["stream"]["room_id"] = d.get('roomId')
                    self.result["stream"]["titulo"] = d.get('roomTopic')
                    self.result["stream"]["juego"] = d.get('gameTitle')
                    self.result["stream"]["espectadores"] = d.get('viewers') or 0
                    
                    if d.get('alive'):
                        self.result["stream"]["activo"] = True
                        self.result["stream"]["hls_url"] = d.get('hls_src')
                        self.log("🔴 EN VIVO!", level="STREAM")
        except:
            pass

    # ============================================================
    # 5. SCAN COMPLETO
    # ============================================================
    
    def scan_user(self, user_id):
        user_id = str(user_id).strip()
        self.user_id = user_id
        self.result["user_id"] = user_id
        self.result["usuario"]["id"] = user_id
        
        print("\n" + "=" * 70)
        print(f"  📱 BIGO.TV SCANNER v15 - Usuario: {user_id}")
        print("=" * 70)
        
        # 1. Login
        if not self._login():
            self.log("No se pudo iniciar sesión. Continuando sin login...", level="WARN")
        
        # 2. Perfil (con login)
        self._get_profile_with_login(user_id)
        
        # 3. Privacidad (solo si hay login)
        if self.logged_in:
            self._get_privacy_settings()
        
        # 4. Studio
        self._get_studio_info(user_id)
        
        # 5. Enlaces
        self._generate_links(user_id)
        
        # 6. Resumen
        self._print_summary()
        
        return self.result
    
    def _generate_links(self, user_id):
        self.result["enlaces"]["perfil"] = f"{self.base_url}/{user_id}"
        self.result["enlaces"]["perfil_mobile"] = f"{self.base_url}/user/{user_id}"

    # ============================================================
    # 6. RESUMEN
    # ============================================================
    
    def _print_summary(self):
        print("\n" + "=" * 70)
        print("  📋 RESUMEN COMPLETO DE PERFIL")
        print("=" * 70)
        
        u = self.result["usuario"]
        p = self.result["privacidad"]
        
        def fmt(n):
            if n is None: return "N/A"
            if isinstance(n, int) and n > 0: return f"{n:,}"
            if n == "": return "N/A"
            return str(n)
        
        print("\n  👤 USUARIO:")
        print(f"    ┌{'─'*65}┐")
        print(f"    │ ID              : {u['id']}")
        print(f"    │ BIGO ID         : {fmt(u['bigo_id'])}")
        print(f"    │ Nickname        : {fmt(u['nickname'])}")
        print(f"    │ Nivel           : {fmt(u['nivel'])}")
        print(f"    │ ⚧️ Género       : {fmt(u['genero'])}")
        print(f"    │ 🎂 Edad         : {fmt(u['edad'])}")
        print(f"    │ 🌍 País         : {fmt(u['pais'])}")
        print(f"    │ 💰 Semillas     : {fmt(u['semillas'])}")
        if u.get('diamantes'):
            print(f"    │ 💎 Diamantes    : {fmt(u['diamantes'])}")
        if u.get('monedas'):
            print(f"    │ 🪙 Monedas      : {fmt(u['monedas'])}")
        print(f"    │ Seguidores      : {fmt(u['seguidores'])}")
        print(f"    │ Verificado      : {'✅ Sí' if u['verificado'] else '❌ No'}")
        if u.get('biografia'):
            bio = u['biografia'][:50] + '...' if len(u['biografia']) > 50 else u['biografia']
            print(f"    │ Biografía       : {bio}")
        print(f"    └{'─'*65}┘")
        
        if u.get('sala_actual'):
            print(f"\n  🏠 SALA ACTUAL:")
            print(f"    ┌{'─'*65}┐")
            print(f"    │ {u['sala_actual']}")
            print(f"    └{'─'*65}┘")
        
        print("\n  🔒 CONFIGURACIÓN DE PRIVACIDAD:")
        print(f"    ┌{'─'*65}┐")
        labels = {
            'ocultar_prueba_juego': 'Ocultar Prueba de juego',
            'ocultar_mascota': 'Esconder mi mascota',
            'desactivar_chat_video': 'Desactivar chat de video',
            'no_molestar_extraños': 'No molestar a extraños',
            'colapsar_mensajes_extraños': 'Colapsar mensajes extraños',
            'no_aceptar_invitaciones_extraños': 'No aceptar invitaciones',
            'grabacion_momentos_vivo': 'Grabación de momentos',
            'ocultar_ubicacion': 'Ocultar ubicación',
            'ocultar_estado_online': 'Ocultar estado online',
            'ocultar_modelo_dispositivo': 'Ocultar modelo de dispositivo',
            'ocultar_tiempo_activo': 'Ocultar tiempo activo',
            'ocultar_estado_familia': 'Ocultar estado a familia',
            'ocultar_realmatch': 'Ocultar Realmatch',
        }
        for key, label in labels.items():
            value = p.get(key)
            if value is True:
                status = "🔒 Oculto / Activado"
            elif value is False:
                status = "👁️ Visible / Desactivado"
            else:
                status = "❓ Desconocido"
            print(f"    │ {label:30} : {status}")
        print(f"    └{'─'*65}┘")
        
        # Stream
        s = self.result["stream"]
        print("\n  📡 STREAM:")
        print(f"    ┌{'─'*65}┐")
        estado = '🔴 EN VIVO' if s['activo'] else '⚫ OFFLINE'
        print(f"    │ Estado          : {estado}")
        print(f"    │ Room ID         : {fmt(s['room_id'])}")
        print(f"    │ Título          : {fmt(s['titulo'])}")
        print(f"    │ Juego           : {fmt(s['juego'])}")
        print(f"    │ Espectadores    : {fmt(s['espectadores'])}")
        print(f"    └{'─'*65}┘")
        
        # Enlaces
        print(f"\n  🔗 ENLACES:")
        print(f"    ┌{'─'*65}┐")
        print(f"    │ Perfil          : {self.result['enlaces']['perfil']}")
        print(f"    │ Perfil móvil    : {self.result['enlaces']['perfil_mobile']}")
        print(f"    └{'─'*65}┘")
        
        print("\n" + "=" * 70)
        print("  ✅ ESCANEO COMPLETADO")
        print("=" * 70)
    
    def close(self):
        try:
            self.driver.quit()
        except:
            pass


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           BIGO.TV SCANNER v15 - Login + Extracción Completa     ║
║     Semillas | Diamantes | Privacidad | Sala | Perfil           ║
║                  USO AUTORIZADO SOLAMENTE                        ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = input("  Ingrese el ID del usuario a escanear: ").strip()
    
    if not user_id:
        print("\n  ❌ Error: Debe ingresar un ID.")
        sys.exit(1)
    
    scanner = BigoLoginScanner(verbose=True, headless=False)
    try:
        result = scanner.scan_user(user_id)
        
        filename = f"bigo_fullscan_v15_{user_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n  📁 Resultados guardados en: {filename}")
        
    finally:
        scanner.close()


if __name__ == "__main__":
    main()
