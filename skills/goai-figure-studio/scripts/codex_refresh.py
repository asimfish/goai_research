"""Refresh a Codex ChatGPT login the way the CLI does (refresh_token grant). Prints status only — never a token."""
import json
import os
import shutil
import sys
import time
from urllib import error, request

home = os.environ.get('CODEX_HOME') or os.path.expanduser('~/.codex')
p = os.path.join(home, 'auth.json')
a = json.load(open(p))
rt = a['tokens']['refresh_token']
data = json.dumps({'client_id': 'app_EMoamEEZ73f0CkXaXp7hrann', 'grant_type': 'refresh_token',
                   'refresh_token': rt, 'scope': 'openid profile email'}).encode()
req = request.Request('https://auth.openai.com/oauth/token', data=data, headers={'Content-Type': 'application/json'})
proxy = os.environ.get('HTTPS_PROXY')
opener = request.build_opener(request.ProxyHandler({'https': proxy, 'http': proxy} if proxy else {}))
try:
    r = opener.open(req, timeout=60)
    body = json.loads(r.read())
    print('refresh ok; response keys:', sorted(body))
    shutil.copy2(p, p + '.bak_refresh_' + time.strftime('%Y%m%dT%H%M%S'))
    a['tokens']['access_token'] = body['access_token']
    a['tokens']['refresh_token'] = body.get('refresh_token', rt)
    if body.get('id_token'):
        a['tokens']['id_token'] = body['id_token']
    a['last_refresh'] = time.strftime('%Y-%m-%dT%H:%M:%S.000000Z', time.gmtime())
    json.dump(a, open(p, 'w'), indent=2)
    print('auth.json updated')
except error.HTTPError as e:
    txt = e.read()[:300].decode(errors='replace')
    print('refresh HTTP', e.code, txt.replace(rt, '<rt>'))
    sys.exit(1)
except Exception as e:  # noqa: BLE001
    print('refresh failed', type(e).__name__, str(e)[:200])
    sys.exit(1)
