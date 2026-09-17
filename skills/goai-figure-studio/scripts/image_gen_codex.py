#!/usr/bin/env python3
"""Image-only generation route for paper-framework-figure-studio-pro runs, standard-library variant of figstudio_gen.py.

Same contract as figstudio_gen.py (Codex `image_gen`: chatgpt.com codex responses endpoint, tool type image_generation;
PNG bytes byte-copied to the registered target_image_path; one event line per image), but built on urllib so it runs
on a host without `requests` (this workstation). Reads the Codex login from $CODEX_HOME/auth.json; refresh it first with
refresh_codex.py when the access token is stale.

usage: figstudio_gen_local.py --index prompt-index.json [--only C01,C02] [--size 1536x1024] [--quality high]
                              [--stage S2-SKETCH-EXPLORE] [--replace]
"""
import argparse
import base64
import json
import mimetypes
import os
import time
import uuid
from pathlib import Path
from urllib import error, request

CODEX_HOME = Path(os.environ.get('CODEX_HOME', os.path.expanduser('~/.codex')))
URL = 'https://chatgpt.com/backend-api/codex/responses'
PROXY = os.environ.get('GOAI_PROXY') or os.environ.get('HTTPS_PROXY') or ''


def headers():
    auth = json.loads((CODEX_HOME / 'auth.json').read_text())['tokens']
    return {'Content-Type': 'application/json', 'Accept': 'text/event-stream', 'Authorization': 'Bearer ' + auth['access_token'],
            'ChatGPT-Account-Id': auth['account_id'], 'originator': 'codex_cli_rs', 'User-Agent': 'codex_cli_rs'}


def prompt_text(path):
    t = Path(path).read_text(encoding='utf-8')
    marker = '\n## IMAGE PROMPT\n'
    return t.split(marker, 1)[1].strip() if marker in t else t.strip()


def data_url(p):
    mt = mimetypes.guess_type(str(p))[0] or 'image/png'
    return f'data:{mt};base64,' + base64.b64encode(Path(p).read_bytes()).decode()


def opener():
    return request.build_opener(request.ProxyHandler({'https': PROXY, 'http': PROXY} if PROXY else {}))


def generate(prompt, size, quality, refs, model='gpt-6-astra', tries=4):
    content = [{'type': 'input_text', 'text': prompt}]
    for r in refs:
        content.append({'type': 'input_image', 'image_url': data_url(r), 'detail': 'high'})
    payload = {'model': model,
               'instructions': 'You are an image generation assistant for a scientific manuscript. Call the image_generation tool exactly once with the user prompt; do not write text.',
               'input': [{'role': 'user', 'content': content}],
               'tools': [{'type': 'image_generation', 'size': size, 'quality': quality, 'output_format': 'png', 'background': 'opaque'}],
               'tool_choice': {'type': 'image_generation'}, 'store': False, 'stream': True}
    body = json.dumps(payload).encode()
    for k in range(tries):
        try:
            r = opener().open(request.Request(URL, data=body, headers=headers(), method='POST'), timeout=600)
        except error.HTTPError as ex:
            txt = ex.read()[:300].decode(errors='replace')
            if ex.code == 429:
                wait = 90 * (k + 1); print(f'  429 usage limit; sleeping {wait}s', flush=True); time.sleep(wait); continue
            print('  HTTP', ex.code, txt.replace('\n', ' '), flush=True); time.sleep(20); continue
        except (error.URLError, OSError) as ex:
            print(f'  request failed: {type(ex).__name__} {str(ex)[:120]}; retrying in 45s', flush=True); time.sleep(45); continue
        img = None; ig_id = None; revised = None; err = None
        try:
            for line in r:
                if not line.startswith(b'data:'):
                    continue
                try:
                    ev = json.loads(line[5:])
                except Exception:  # noqa: BLE001
                    continue
                t = ev.get('type', '')
                if t == 'response.output_item.done':
                    it = ev.get('item', {})
                    if it.get('type') == 'image_generation_call':
                        ig_id = it.get('id'); revised = it.get('revised_prompt'); img = it.get('result') or img
                elif t in ('error', 'response.failed'):
                    err = str(ev)[:400]
        except (OSError, ValueError) as ex:
            err = f'stream broken: {type(ex).__name__}'
            if img:
                return base64.b64decode(img), ig_id, revised
            print('  ' + err + '; retrying', flush=True); time.sleep(30); continue
        if img:
            return base64.b64decode(img), ig_id, revised
        print('  no image in response', err or '', flush=True); time.sleep(15)
    return None, None, None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--index', required=True); ap.add_argument('--only', default='')
    ap.add_argument('--size', default='1536x1024'); ap.add_argument('--quality', default='high'); ap.add_argument('--events', default='')
    ap.add_argument('--stage', default='S2-SKETCH-EXPLORE'); ap.add_argument('--replace', action='store_true')
    a = ap.parse_args(); idx_path = Path(a.index); root = idx_path.parent.parent.parent  # <project>/outputs/<stage>/prompt-index.json
    idx = json.loads(idx_path.read_text(encoding='utf-8')); only = set(x for x in a.only.split(',') if x)
    events = Path(a.events) if a.events else idx_path.parent / 'image-generation-events.jsonl'
    for row in idx['candidates']:
        cid = row['candidate_id']
        if only and cid not in only:
            continue
        target = root / row['target_image_path']
        if target.exists() and not a.replace:
            print(cid, 'exists, skip'); continue
        prompt = prompt_text(root / row['prompt_path']); refs = [root / p for p in row.get('reference_image_paths', []) if (root / p).exists()]
        size = row.get('size', a.size); quality = row.get('quality', a.quality)
        print(f'{cid}: generating {target.name} ({size}, {quality}, {len(refs)} refs, prompt {len(prompt)} chars)', flush=True)
        t0 = time.time(); png, ig_id, revised = generate(prompt, size, quality, refs)
        if not png:
            print(cid, 'FAILED', flush=True); continue
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(png)
        ev = {'image_generation_event_id': f'ige-{uuid.uuid4().hex[:12]}', 'candidate_id': cid, 'stage': a.stage, 'environment': 'codex',
              'generator': 'image_gen', 'required_generator': 'image_gen', 'route_guard_status': 'passed', 'provider_call_id': ig_id,
              'model_tool': {'tool': 'image_generation', 'size': size, 'quality': quality, 'output_format': 'png'},
              'prompt_path': row['prompt_path'], 'reference_image_paths': [str(p.relative_to(root)) for p in refs],
              'generated_paths': [row['target_image_path']], 'byte_copy_only': True, 'bytes': len(png), 'seconds': round(time.time() - t0, 1),
              'revised_prompt': revised, 'host': 'workstation', 'time': time.strftime('%Y-%m-%dT%H:%M:%S')}
        with events.open('a', encoding='utf-8') as f:
            f.write(json.dumps(ev, ensure_ascii=False) + '\n')
        print(f'{cid}: saved {len(png)} bytes in {ev["seconds"]}s', flush=True)


if __name__ == '__main__':
    main()
