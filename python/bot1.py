#!/usr/bin/env python3
"""
Bigo.tv FULL SCANNER v9 - Dispositivo + Historial Completo
Busca dispositivo, UID, país, ciudad en múltiples fuentes
USO AUTORIZADO SOLAMENTE - Pentesting ético
"""

import requests
import json
import sys
import re
import time
import hashlib
import base64
from urllib.parse import urlparse, urlencode, quote, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


class BigoFullScannerV9:
    def __init__(self, verbose=True):
        self.base_url = "https://www.bigo.tv"
        self.api_url = "https://ta.bigo.tv/official_website"
        self.login_url = "https://ta.bigo.tv/official_website_login"
        self.verbose = verbose
        self.user_id = None
        
        # Session principal
        self.s = requests.Session()
        self.s.timeout = 20
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": self.base_url,
            "Referer": self.base_url + "/",
            "DNT": "1",
            "Connection": "keep-alive",
            "X-Requested-With": "XMLHttpRequest",
        })
        
        # Session HTML
        self.html_s = requests.Session()
        self.html_s.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        
        # Servicios de geolocalización
        self.geo_services = [
            "http://ip-api.com/json/",
            "http://ipinfo.io/",
        ]
        
        self.result = {
            "scan_time": datetime.now().isoformat(),
            "user_id": None,
            "usuario": {
                "id": None,
                "uid": None,
                "bigo_id": None,
                "nickname": None,
                "avatar": None,
                "nivel": 0,
                "genero": None,
                "edad": None,
                "pais": None,
                "pais_codigo": None,
                "ciudad": None,
                "seguidores": 0,
                "siguiendo": 0,
                "biografia": None,
                "verificado": False,
                "balance": 0,
                "fecha_registro": None,
                "ultima_conexion": None,
                "telefono": None,
                "email": None,
                "dispositivo": None,
                "dispositivo_nombre": None,
                "so": None,
                "ip": None,
                "uid_real": None,
            },
            "historial": {
                "paises": [],
                "ciudades": [],
                "dispositivos": [],
                "ips": [],
                "uids": [],
                "streams_historial": [],
            },
            "geo_info": {},
            "stream": {
                "activo": False,
                "room_id": None,
                "titulo": None,
                "juego": None,
                "espectadores": 0,
                "hls_url": None,
                "alive": 0,
                "streamer_id": None,
                "device_type": None,
            },
            "estadisticas": {
                "vistas_totales": 0,
                "total_likes": 0,
                "total_diamantes": 0,
            },
            "endpoints": {
                "encontrados": [],
                "totales": 0,
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
                "MAP": "  🗺️",
                "GAME": "  🎮",
                "FIND": "  🔍",
                "SOCIAL": "  🌐",
                "EMAIL": "  📧",
                "PHONE": "  📱",
                "DEVICE": "  💻",
                "LOCATION": "  📍",
                "HISTORY": "  📜",
                "UID": "  🆔",
            }.get(level, "  ")
            print(f"{prefix} {msg}", end=end)

    # ============================================================
    # 1. BUSCAR DISPOSITIVO Y UID REAL
    # ============================================================
    
    def _find_device_and_uid(self, user_id):
        """Busca dispositivo y UID real del usuario"""
        self.log("\n[1] 🔍 Buscando Dispositivo y UID Real...", level="DEVICE")
        
        dispositivo_encontrado = None
        uid_real = None
        dispositivo_nombre = None
        
        # Fuente 1: Studio Info (contiene streamer_id)
        url = f"{self.api_url}/studio/getInternalStudioInfo"
        try:
            resp = self.s.post(url, data={"siteId": user_id})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 and data.get("data"):
                    d = data["data"]
                    if d.get('streamerId'):
                        uid_real = d['streamerId']
                        self.log(f"Streamer ID (UID real): {uid_real}", level="UID")
                    if d.get('deviceType'):
                        dispositivo_nombre = d['deviceType']
                        self.log(f"Tipo de dispositivo: {dispositivo_nombre}", level="DEVICE")
        except:
            pass
        
        # Fuente 2: usercenter/getUserInfo
        url = f"{self.api_url}/usercenter/getUserInfo"
        for param in ["userId", "uid", "id"]:
            try:
                resp = self.s.get(url, params={param: user_id})
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0 and data.get("data"):
                        d = data["data"]
                        if d.get('device'):
                            dispositivo_encontrado = d['device']
                            self.log(f"Dispositivo (API): {dispositivo_encontrado}", level="DEVICE")
                        if d.get('deviceName') or d.get('device_name'):
                            dispositivo_nombre = d.get('deviceName') or d.get('device_name')
                            self.log(f"Nombre dispositivo: {dispositivo_nombre}", level="DEVICE")
                        if d.get('uid'):
                            uid_real = d['uid']
                            self.log(f"UID (API): {uid_real}", level="UID")
                        break
            except:
                pass
        
        # Fuente 3: OUserCenter/getUserInfoStudio
        url = f"{self.api_url}/OUserCenter/getUserInfoStudio"
        for param in ["userId", "siteId", "uid"]:
            try:
                resp = self.s.get(url, params={param: user_id})
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0 and data.get("data"):
                        d = data["data"]
                        if d.get('device'):
                            dispositivo_encontrado = d['device']
                            self.log(f"Dispositivo (OUser): {dispositivo_encontrado}", level="DEVICE")
                        if d.get('deviceName'):
                            dispositivo_nombre = d['deviceName']
                            self.log(f"Nombre dispositivo: {dispositivo_nombre}", level="DEVICE")
                        if d.get('uid'):
                            uid_real = d['uid']
                            self.log(f"UID (OUser): {uid_real}", level="UID")
                        break
            except:
                pass
        
        # Fuente 4: user/device endpoint
        url = f"{self.api_url}/user/device"
        for param in ["userId", "uid", "id"]:
            try:
                resp = self.s.get(url, params={param: user_id})
                if resp.status_code == 200:
                    data = resp.json()
                    if data and isinstance(data, dict):
                        if data.get('deviceId') or data.get('device_id'):
                            dispositivo_encontrado = data.get('deviceId') or data.get('device_id')
                            self.log(f"Dispositivo (device): {dispositivo_encontrado}", level="DEVICE")
                        if data.get('deviceName'):
                            dispositivo_nombre = data['deviceName']
                            self.log(f"Nombre dispositivo: {dispositivo_nombre}", level="DEVICE")
                        break
            except:
                pass
        
        # Fuente 5: user/sessions (para ver dispositivos activos)
        url = f"{self.api_url}/user/sessions"
        try:
            resp = self.s.get(url, params={"userId": user_id})
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, dict):
                    sessions = data.get('data', []) or data.get('sessions', [])
                    if sessions and isinstance(sessions, list):
                        for session in sessions[:3]:
                            if session.get('deviceId') or session.get('device_id'):
                                device = session.get('deviceId') or session.get('device_id')
                                self.log(f"Sesión dispositivo: {device}", level="DEVICE")
                                if not dispositivo_encontrado:
                                    dispositivo_encontrado = device
                            if session.get('deviceName'):
                                self.log(f"Sesión nombre: {session['deviceName']}", level="DEVICE")
        except:
            pass
        
        # Fuente 6: HTML - buscar en window.__BIGOLIVE__
        url = f"{self.base_url}/user/{user_id}"
        try:
            resp = self.html_s.get(url)
            if resp.status_code == 200:
                html = resp.text
                json_match = re.search(r'window\.__BIGOLIVE__\s*=\s*({.*?});', html, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        state = data.get('state', {})
                        user_info = state.get('userInfo', {})
                        if user_info.get('device'):
                            dispositivo_encontrado = user_info['device']
                            self.log(f"Dispositivo (HTML): {dispositivo_encontrado}", level="DEVICE")
                        if user_info.get('uid'):
                            uid_real = user_info['uid']
                            self.log(f"UID (HTML): {uid_real}", level="UID")
                    except:
                        pass
                
                # Buscar patrones de UUID en el HTML
                uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
                uuids = re.findall(uuid_pattern, html, re.I)
                if uuids and not dispositivo_encontrado:
                    dispositivo_encontrado = uuids[0]
                    self.log(f"Dispositivo (UUID HTML): {dispositivo_encontrado}", level="DEVICE")
        except:
            pass
        
        # Guardar resultados
        if dispositivo_encontrado:
            self.result["usuario"]["dispositivo"] = dispositivo_encontrado
        if dispositivo_nombre:
            self.result["usuario"]["dispositivo_nombre"] = dispositivo_nombre
        if uid_real:
            self.result["usuario"]["uid_real"] = uid_real
        
        return dispositivo_encontrado, uid_real
    
    # ============================================================
    # 2. HISTORIAL DE STREAMS (para ver dispositivos usados)
    # ============================================================
    
    def _get_stream_history(self, user_id):
        """Obtiene historial de streams donde puede aparecer el dispositivo"""
        self.log("\n[2] 📜 Buscando Historial de Streams...", level="HISTORY")
        
        historial_streams = []
        dispositivos_en_streams = set()
        
        endpoints = [
            f"{self.api_url}/OInterfaceWeb/vedioList/5?uid={user_id}",
            f"{self.api_url}/OInterfaceWeb/vedioList/11?uid={user_id}",
            f"{self.api_url}/OInterfaceWeb/vedioList/72?uid={user_id}",
            f"{self.api_url}/user/history?userId={user_id}",
        ]
        
        for url in endpoints:
            try:
                resp = self.s.get(url, timeout=10)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if data and isinstance(data, dict):
                            items = data.get('data', []) or data.get('list', []) or data.get('items', [])
                            if isinstance(items, list):
                                for item in items[:20]:  # Solo los últimos 20
                                    if isinstance(item, dict):
                                        stream_info = {
                                            'room_id': item.get('room_id') or item.get('roomId'),
                                            'title': item.get('title') or item.get('roomTopic'),
                                            'date': item.get('create_time') or item.get('startTime'),
                                            'views': item.get('view_count') or item.get('views'),
                                            'duration': item.get('duration'),
                                            'device': item.get('device') or item.get('deviceType'),
                                            'device_name': item.get('deviceName'),
                                        }
                                        historial_streams.append(stream_info)
                                        
                                        if stream_info.get('device'):
                                            dispositivos_en_streams.add(stream_info['device'])
                                        if stream_info.get('device_name'):
                                            dispositivos_en_streams.add(stream_info['device_name'])
                    except:
                        pass
            except:
                pass
        
        self.result["historial"]["streams_historial"] = historial_streams
        if dispositivos_en_streams:
            self.log(f"Dispositivos en streams: {', '.join(list(dispositivos_en_streams)[:3])}", level="DEVICE")
            if not self.result["usuario"]["dispositivo"]:
                self.result["usuario"]["dispositivo"] = list(dispositivos_en_streams)[0]
        
        return historial_streams
    
    # ============================================================
    # 3. BUSCAR PAÍS Y CIUDAD
    # ============================================================
    
    def _find_country(self, user_id):
        """Busca país en múltiples fuentes"""
        self.log("\n[3] 🌍 Buscando País y Ciudad...", level="LOCATION")
        
        pais_encontrado = None
        ciudad_encontrada = None
        ip_encontrada = None
        
        # Fuente 1: HTML
        url = f"{self.base_url}/user/{user_id}"
        try:
            resp = self.html_s.get(url)
            if resp.status_code == 200:
                html = resp.text
                
                # Buscar en JSON embebido
                json_match = re.search(r'window\.__BIGOLIVE__\s*=\s*({.*?});', html, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        state = data.get('state', {})
                        user_info = state.get('userInfo', {})
                        if user_info.get('country'):
                            pais_encontrado = user_info['country']
                            self.log(f"País (BIGOLIVE): {pais_encontrado}", level="OK")
                        if user_info.get('city'):
                            ciudad_encontrada = user_info['city']
                            self.log(f"Ciudad (BIGOLIVE): {ciudad_encontrada}", level="OK")
                    except:
                        pass
        except:
            pass
        
        # Fuente 2: queryCountry
        if not pais_encontrado:
            try:
                resp = self.s.get(f"{self.api_url}/usercenter/queryCountry", timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('country'):
                        pais_encontrado = data['country']
                        self.log(f"País (queryCountry): {pais_encontrado}", level="OK")
            except:
                pass
        
        # Fuente 3: OUserCenter
        if not pais_encontrado:
            url = f"{self.api_url}/OUserCenter/getUserInfoStudio"
            for param in ["userId", "siteId", "uid"]:
                try:
                    resp = self.s.get(url, params={param: user_id})
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("code") == 0 and data.get("data"):
                            d = data["data"]
                            if d.get('country'):
                                pais_encontrado = d['country']
                                self.log(f"País (OUser): {pais_encontrado}", level="OK")
                            if d.get('city'):
                                ciudad_encontrada = d['city']
                                self.log(f"Ciudad (OUser): {ciudad_encontrada}", level="OK")
                            if d.get('ip'):
                                ip_encontrada = d['ip']
                            break
                except:
                    pass
        
        # Fuente 4: GeoIP
        if ip_encontrada or not pais_encontrado:
            ip_to_check = ip_encontrada or self._get_public_ip()
            if ip_to_check:
                geo = self._geoip_lookup(ip_to_check)
                if geo:
                    self.result["geo_info"] = geo
                    if geo.get('country') and not pais_encontrado:
                        pais_encontrado = geo['country']
                        self.log(f"País (GeoIP): {pais_encontrado}", level="OK")
                    if geo.get('city') and not ciudad_encontrada:
                        ciudad_encontrada = geo['city']
                        self.log(f"Ciudad (GeoIP): {ciudad_encontrada}", level="OK")
        
        if pais_encontrado:
            self.result["usuario"]["pais"] = pais_encontrado
        if ciudad_encontrada:
            self.result["usuario"]["ciudad"] = ciudad_encontrada
        if ip_encontrada:
            self.result["usuario"]["ip"] = ip_encontrada
        
        return pais_encontrado, ciudad_encontrada
    
    def _get_public_ip(self):
        try:
            resp = self.s.get("https://api.ipify.org?format=json", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('ip')
        except:
            pass
        return None
    
    def _geoip_lookup(self, ip):
        try:
            url = f"http://ip-api.com/json/{ip}"
            resp = self.s.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    return {
                        'ip': ip,
                        'country': data.get('country'),
                        'countryCode': data.get('countryCode'),
                        'city': data.get('city'),
                        'region': data.get('regionName'),
                        'timezone': data.get('timezone'),
                        'lat': data.get('lat'),
                        'lon': data.get('lon'),
                        'isp': data.get('isp'),
                        'org': data.get('org'),
                    }
        except:
            pass
        return None

    # ============================================================
    # 4. ENDPOINTS PRINCIPALES
    # ============================================================
    
    def _endpoint_studio_info(self, user_id):
        self.log("\n[4] getInternalStudioInfo (POST)", level="STREAM")
        url = f"{self.api_url}/studio/getInternalStudioInfo"
        
        try:
            resp = self.s.post(url, data={"siteId": user_id})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 and data.get("data"):
                    d = data["data"]
                    self.log(f"Room ID: {d.get('roomId')}", level="OK")
                    self.log(f"Nickname: {d.get('nick_name')}", level="OK")
                    
                    self.result["stream"]["room_id"] = d.get('roomId')
                    self.result["stream"]["titulo"] = d.get('roomTopic')
                    self.result["stream"]["juego"] = d.get('gameTitle')
                    self.result["stream"]["espectadores"] = d.get('viewers') or 0
                    self.result["stream"]["alive"] = d.get('alive')
                    
                    if d.get('alive'):
                        self.result["stream"]["activo"] = True
                        self.result["stream"]["hls_url"] = d.get('hls_src')
                    
                    if d.get('nick_name'):
                        self.result["usuario"]["nickname"] = d['nick_name']
                    if d.get('clientBigoId'):
                        self.result["usuario"]["bigo_id"] = d['clientBigoId']
                    if d.get('streamerId'):
                        self.result["usuario"]["uid_real"] = d['streamerId']
                    
                    return data
        except:
            pass
        return None
    
    def _endpoint_user_info(self, user_id):
        self.log("\n[5] getUserInfo (GET)", level="USER")
        url = f"{self.api_url}/usercenter/getUserInfo"
        
        for param in ["userId", "uid", "id"]:
            try:
                resp = self.s.get(url, params={param: user_id})
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if data.get("code") == 0 and data.get("data"):
                            d = data["data"]
                            self.log(f"Nickname: {d.get('nick_name')}", level="OK")
                            if d.get('level'):
                                self.log(f"Nivel: {d.get('level')}", level="OK")
                            if d.get('device'):
                                self.log(f"Dispositivo: {d.get('device')}", level="DEVICE")
                            if d.get('uid'):
                                self.log(f"UID: {d.get('uid')}", level="UID")
                            return data
                    except:
                        pass
            except:
                pass
        return None
    
    def _extract_from_html(self, user_id):
        self.log("\n[6] Extracción HTML", level="FIND")
        url = f"{self.base_url}/user/{user_id}"
        
        try:
            resp = self.html_s.get(url)
            if resp.status_code == 200:
                html = resp.text
                
                # Buscar window.__BIGOLIVE__
                json_match = re.search(r'window\.__BIGOLIVE__\s*=\s*({.*?});', html, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        state = data.get('state', {})
                        user_info = state.get('userInfo', {})
                        if user_info:
                            if user_info.get('country'):
                                self.result["usuario"]["pais"] = user_info['country']
                            if user_info.get('city'):
                                self.result["usuario"]["ciudad"] = user_info['city']
                            if user_info.get('device'):
                                self.result["usuario"]["dispositivo"] = user_info['device']
                            if user_info.get('uid'):
                                self.result["usuario"]["uid_real"] = user_info['uid']
                            self.log(f"Datos extraídos del HTML", level="OK")
                    except:
                        pass
                
                # Buscar UUID en HTML
                uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
                uuids = re.findall(uuid_pattern, html, re.I)
                if uuids and not self.result["usuario"]["dispositivo"]:
                    self.result["usuario"]["dispositivo"] = uuids[0]
                    self.log(f"Dispositivo (UUID): {uuids[0]}", level="DEVICE")
                
                self.log("✓ Extracción HTML completada", level="OK")
        except Exception as e:
            self.log(f"Error: {e}", level="ERROR")
    
    # ============================================================
    # 5. SCAN COMPLETO
    # ============================================================
    
    def scan_user(self, user_id):
        user_id = str(user_id)
        self.user_id = user_id
        self.result["user_id"] = user_id
        self.result["usuario"]["id"] = user_id
        
        print("\n" + "=" * 70)
        print(f"  📱 BIGO.TV FULL SCANNER v9 - Usuario: {user_id}")
        print("=" * 70)
        print("  🔍 Buscando: País, Ciudad, Dispositivo, UID Real, Historial")
        print("=" * 70)
        
        # 1. Buscar dispositivo y UID
        self._find_device_and_uid(user_id)
        
        # 2. Historial de streams
        self._get_stream_history(user_id)
        
        # 3. Buscar país y ciudad
        self._find_country(user_id)
        
        # 4. Endpoints principales
        self._endpoint_studio_info(user_id)
        self._endpoint_user_info(user_id)
        self._extract_from_html(user_id)
        
        # 5. Generar enlaces
        self._generate_links(user_id)
        
        # 6. Resumen
        self._print_summary()
        
        return self.result
    
    def _generate_links(self, user_id):
        self.result["enlaces"]["perfil"] = f"{self.base_url}/{user_id}"
        self.result["enlaces"]["perfil_mobile"] = f"{self.base_url}/user/{user_id}"
        self.result["enlaces"]["app_deeplink"] = f"bigolive://profile?uid={user_id}"
    
    # ============================================================
    # 6. RESUMEN
    # ============================================================
    
    def _print_summary(self):
        print("\n" + "=" * 70)
        print("  📋 RESUMEN COMPLETO DE PERFIL")
        print("=" * 70)
        
        u = self.result["usuario"]
        s = self.result["stream"]
        h = self.result["historial"]
        
        def fmt(n):
            if n is None: return "N/A"
            if isinstance(n, int) and n > 0: return f"{n:,}"
            if n == "": return "N/A"
            return str(n)
        
        print("\n  👤 USUARIO:")
        print(f"    ┌{'─'*65}┐")
        print(f"    │ ID              : {u['id']}")
        print(f"    │ 🆔 UID Real     : {fmt(u['uid_real'])}")
        print(f"    │ BIGO ID         : {fmt(u['bigo_id'])}")
        print(f"    │ Nickname        : {fmt(u['nickname'])}")
        print(f"    │ Nivel           : {fmt(u['nivel'])}")
        print(f"    │ Género          : {fmt(u['genero'])}")
        print(f"    │ Edad            : {fmt(u['edad'])}")
        print(f"    │ 🌍 País         : {fmt(u['pais'])}")
        if u.get('pais_codigo'):
            print(f"    │ Código País     : {u['pais_codigo']}")
        print(f"    │ 🏙️ Ciudad       : {fmt(u['ciudad'])}")
        print(f"    │ Seguidores      : {fmt(u['seguidores'])}")
        print(f"    │ Siguiendo       : {fmt(u['siguiendo'])}")
        print(f"    │ Balance         : {fmt(u['balance'])}")
        print(f"    │ Verificado      : {'✅ Sí' if u['verificado'] else '❌ No'}")
        print(f"    │ 📧 Email        : {fmt(u['email'])}")
        print(f"    │ 📱 Teléfono     : {fmt(u['telefono'])}")
        print(f"    │ 💻 Dispositivo  : {fmt(u['dispositivo'])}")
        if u.get('dispositivo_nombre'):
            print(f"    │ 📱 Nombre       : {u['dispositivo_nombre']}")
        if u.get('so'):
            print(f"    │ SO              : {u['so']}")
        if u.get('ip'):
            print(f"    │ 🌐 IP           : {u['ip']}")
        if u.get('biografia'):
            bio = u['biografia'][:50] + '...' if len(u['biografia']) > 50 else u['biografia']
            print(f"    │ Biografía       : {bio}")
        print(f"    └{'─'*65}┘")
        
        # Historial de cambios
        print("\n  📜 HISTORIAL DE CAMBIOS:")
        print(f"    ┌{'─'*65}┐")
        if h["paises"]:
            print(f"    │ 🌍 Países       : {', '.join(h['paises'])}")
        if h["ciudades"]:
            print(f"    │ 🏙️ Ciudades     : {', '.join(h['ciudades'])}")
        if h["dispositivos"]:
            print(f"    │ 💻 Dispositivos : {len(h['dispositivos'])} encontrados")
            for d in h['dispositivos'][:3]:
                print(f"    │   • {str(d)[:40]}...")
        if h["uids"]:
            print(f"    │ 🆔 UIDs         : {', '.join(h['uids'])}")
        if h["ips"]:
            print(f"    │ 🌐 IPs          : {', '.join(h['ips'])}")
        print(f"    └{'─'*65}┘")
        
        # Streams recientes
        if h["streams_historial"]:
            print(f"\n  📹 STREAMS RECIENTES ({len(h['streams_historial'])}):")
            print(f"    ┌{'─'*65}┐")
            for stream in h["streams_historial"][:5]:
                title = stream.get('title', 'N/A')[:30]
                device = stream.get('device', 'N/A') or stream.get('device_name', 'N/A')
                print(f"    │ • {title}... (Dispositivo: {device[:20]})")
            print(f"    └{'─'*65}┘")
        
        # Geo IP
        if self.result["geo_info"]:
            g = self.result["geo_info"]
            print(f"\n  📍 GEOLOCALIZACIÓN (IP):")
            print(f"    ┌{'─'*65}┐")
            if g.get('isp'):
                print(f"    │ ISP             : {g['isp']}")
            if g.get('org'):
                print(f"    │ Organización    : {g['org']}")
            if g.get('timezone'):
                print(f"    │ Zona Horaria    : {g['timezone']}")
            if g.get('lat') and g.get('lon'):
                print(f"    │ Coordenadas     : {g['lat']}, {g['lon']}")
                print(f"    │ Google Maps     : https://www.google.com/maps?q={g['lat']},{g['lon']}")
            print(f"    └{'─'*65}┘")
        
        # Stream
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
        print(f"    │ Deeplink        : {self.result['enlaces']['app_deeplink']}")
        print(f"    └{'─'*65}┘")
        
        if u['avatar']:
            print(f"\n  🖼️  AVATAR: {u['avatar'][:80]}...")
        
        print("\n" + "=" * 70)
        print("  ✅ ESCANEO COMPLETADO")
        print("=" * 70)


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           BIGO.TV FULL SCANNER v9 - Dispositivo + UID Real      ║
║        País | Ciudad | Dispositivo | UID | Historial            ║
║                  USO AUTORIZADO SOLAMENTE                        ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = input("  Ingrese el BIGO ID del usuario: ").strip()
    
    if not user_id or not user_id.isdigit():
        print("\n  ❌ Error: El ID debe ser un número.")
        sys.exit(1)
    
    scanner = BigoFullScannerV9(verbose=True)
    result = scanner.scan_user(user_id)
    
    filename = f"bigo_fullscan_v9_{user_id}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n  📁 Resultados guardados en: {filename}")
    print(f"  📁 Dispositivo: {result['usuario']['dispositivo'] or 'N/A'}")
    print(f"  📁 UID Real: {result['usuario']['uid_real'] or 'N/A'}")
    print(f"  📁 País: {result['usuario']['pais'] or 'N/A'}")
    print(f"  📁 Ciudad: {result['usuario']['ciudad'] or 'N/A'}")


if __name__ == "__main__":
    main()
