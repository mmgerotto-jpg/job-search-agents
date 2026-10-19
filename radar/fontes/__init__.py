"""HTTP com verificação de SSL, retry e ritmo educado. Só endpoints públicos, sem login."""
import json
import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (compatible; job-radar/1.0; personal use)"
_ultimo = {"t": 0.0}
PAUSA = 0.6


def pegar(url, tentativas=3, timeout=30, dados=None, cabecalhos=None):
    ultimo = None
    for i in range(tentativas):
        dt = PAUSA - (time.time() - _ultimo["t"])
        if dt > 0:
            time.sleep(dt)
        _ultimo["t"] = time.time()
        req = urllib.request.Request(url, data=dados, headers={"User-Agent": UA, **(cabecalhos or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 400, 401, 403):
                raise
            ultimo = e
        except Exception as e:
            ultimo = e
        time.sleep(2 * (i + 1))
    raise ultimo


def json_de(url, **kw):
    return json.loads(pegar(url, **kw))
