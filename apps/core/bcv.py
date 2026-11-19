"""
Cliente e integración de la Tasa Oficial del Banco Central de Venezuela (BCV).

Consulta las tasas oficiales de USD y EUR publicadas por el BCV con múltiples
fuentes de respaldo:
1. Portal oficial del BCV (https://www.bcv.org.ve/)
2. API DolarApi Venezuela Oficial BCV (https://ve.dolarapi.com/v1/dolares/oficial)
3. Respaldo en caché local para respuesta instantánea y modo sin conexión.
"""

import json
import re
import ssl
import time
import urllib.request
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.utils import timezone

CACHE_TTL_SECONDS = 1800  # 30 minutos
CACHE_FILE = Path(settings.BASE_DIR) / '.bcv_cache.json'

DEFAULT_USD_COP = 4200.0

# Valores iniciales de respaldo si aún no se ha consultado la red
DEFAULT_BCV = {
    'usd': 65.0000,
    'eur': 70.2000,
    'usd_cop': DEFAULT_USD_COP,
    'cop': round(65.0000 / DEFAULT_USD_COP, 6),
    'ves_cop': round(DEFAULT_USD_COP / 65.0000, 4),
    'fecha': timezone.localdate().isoformat(),
    'actualizado': '',
    'fuente': 'BCV (Referencia local)',
    'ok': True,
}

_MEM_CACHE = {
    'timestamp': 0.0,
    'data': None,
}


def _parse_decimal_ve(val):
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        d = Decimal(s)
        return float(round(d, 4)) if d > 0 else None
    except (InvalidOperation, ValueError):
        return None


def _http_get(url, timeout=4.0):
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) TributoVE/2.0',
            'Accept': 'application/json, text/html, */*',
        },
    )
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read().decode('utf-8', errors='ignore')


def _fetch_from_bcv_portal():
    """Extrae USD y EUR directamente de https://www.bcv.org.ve/."""
    html = _http_get('https://www.bcv.org.ve/', timeout=4.5)
    m_usd = re.search(r'id=["\']dolar["\'][\s\S]{0,600}?<strong>\s*([0-9.,]+)\s*</strong>', html, re.IGNORECASE)
    m_eur = re.search(r'id=["\']euro["\'][\s\S]{0,600}?<strong>\s*([0-9.,]+)\s*</strong>', html, re.IGNORECASE)
    usd = _parse_decimal_ve(m_usd.group(1)) if m_usd else None
    eur = _parse_decimal_ve(m_eur.group(1)) if m_eur else None
    if not usd:
        raise ValueError('No se encontró #dolar en BCV')

    m_fecha = re.search(r'class=["\']date-display-single["\'][^>]*content=["\'](\d{4}-\d{2}-\d{2})', html)
    fecha = m_fecha.group(1) if m_fecha else timezone.localdate().isoformat()
    if not eur:
        eur = round(usd * 1.08, 4)

    return {
        'usd': usd,
        'eur': eur,
        'fecha': fecha,
        'actualizado': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'fuente': 'Banco Central de Venezuela (bcv.org.ve)',
        'ok': True,
    }


def _fetch_from_dolarapi():
    """Consulta la tasa oficial BCV a través de ve.dolarapi.com."""
    raw_usd = _http_get('https://ve.dolarapi.com/v1/dolares/oficial', timeout=4.0)
    data_usd = json.loads(raw_usd)
    usd = _parse_decimal_ve(data_usd.get('promedio'))
    if not usd:
        raise ValueError('Promedio USD inválido en DolarApi')

    eur = None
    try:
        raw_eur = _http_get('https://ve.dolarapi.com/v1/euros/oficial', timeout=3.0)
        data_eur = json.loads(raw_eur)
        eur = _parse_decimal_ve(data_eur.get('promedio'))
    except Exception:
        pass

    if not eur:
        eur = round(usd * 1.08, 4)

    fecha_raw = str(data_usd.get('fechaActualizacion') or '')[:10]
    fecha = fecha_raw if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_raw) else timezone.localdate().isoformat()

    return {
        'usd': usd,
        'eur': eur,
        'fecha': fecha,
        'actualizado': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'fuente': 'BCV Oficial (DolarApi VE)',
        'ok': True,
    }


def _load_disk_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            if isinstance(saved, dict) and saved.get('usd'):
                return saved
        except Exception:
            pass
    return None


def _save_disk_cache(data):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


def _fetch_usd_cop(fallback=DEFAULT_USD_COP):
    """Obtiene la TRM oficial (COP por 1 USD) para calcular la paridad COP/VES."""
    try:
        raw = _http_get('https://co.dolarapi.com/v1/trm', timeout=3.0)
        data = json.loads(raw)
        val = _parse_decimal_ve(data.get('valor'))
        if val and val > 100:
            return float(val)
    except Exception:
        pass
    return float(fallback)


def _enriquecer_cop(data, permitir_red=False):
    """Garantiza que el diccionario BCV incluya las tasas cruzadas COP ↔ VES."""
    if not isinstance(data, dict):
        return dict(DEFAULT_BCV)
    usd = float(data.get('usd') or DEFAULT_BCV['usd'])
    usd_cop = data.get('usd_cop')
    if not usd_cop and permitir_red:
        usd_cop = _fetch_usd_cop()
    usd_cop = float(usd_cop or DEFAULT_USD_COP)
    data['usd_cop'] = round(usd_cop, 4)
    data['cop'] = round(usd / usd_cop, 6) if usd_cop > 0 else 0.0
    data['ves_cop'] = round(usd_cop / usd, 4) if usd > 0 else 0.0
    return data


def obtener_tasas_bcv(forzar=False, permitir_red=True):
    """
    Devuelve un diccionario con la tasa BCV vigente:
    {
        'usd': float,
        'eur': float,
        'usd_cop': float,
        'cop': float,      # 1 COP en Bs.
        'ves_cop': float,  # 1 Bs. en COP
        'fecha': 'YYYY-MM-DD',
        'actualizado': 'DD/MM/YYYY HH:MM',
        'fuente': str,
        'ok': bool,
    }
    """
    now = time.time()
    if not forzar and _MEM_CACHE['data'] and (now - _MEM_CACHE['timestamp'] < CACHE_TTL_SECONDS):
        return _enriquecer_cop(_MEM_CACHE['data'], permitir_red=False)

    if not _MEM_CACHE['data']:
        disk = _load_disk_cache()
        if disk:
            disk = _enriquecer_cop(disk, permitir_red=False)
            _MEM_CACHE['data'] = disk
            _MEM_CACHE['timestamp'] = now - (CACHE_TTL_SECONDS // 2)
            if not forzar and not permitir_red:
                return disk

    if not permitir_red:
        return _enriquecer_cop(_MEM_CACHE['data'] or dict(DEFAULT_BCV), permitir_red=False)

    for fetcher in (_fetch_from_bcv_portal, _fetch_from_dolarapi):
        try:
            res = fetcher()
            if res and res.get('usd'):
                prev_cop = (_MEM_CACHE['data'] or {}).get('usd_cop') or DEFAULT_USD_COP
                res['usd_cop'] = _fetch_usd_cop(fallback=prev_cop)
                res = _enriquecer_cop(res, permitir_red=False)
                _MEM_CACHE['data'] = res
                _MEM_CACHE['timestamp'] = now
                _save_disk_cache(res)
                return res
        except Exception:
            continue

    fallback = _MEM_CACHE['data'] or _load_disk_cache() or dict(DEFAULT_BCV)
    return _enriquecer_cop(fallback, permitir_red=False)
