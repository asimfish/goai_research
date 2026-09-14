"""把 deck.html + p/ + d/ 打包成一个可离线双击打开的单文件 HTML。"""
import base64, glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'deck.html'), encoding='utf-8').read()

# 1) 所有图片 -> data URI
imgs = {}
for p in sorted(glob.glob(os.path.join(HERE, 'p', '*.webp'))) + sorted(glob.glob(os.path.join(HERE, 'd', '*.webp'))):
    key = os.path.relpath(p, HERE).replace(os.sep, '/')
    imgs[key] = 'data:image/webp;base64,' + base64.b64encode(open(p, 'rb').read()).decode('ascii')
blob = '{' + ','.join('"%s":"%s"' % (k, v) for k, v in imgs.items()) + '}'

# 2) 拆出 head（title/link/style）与 body
i = src.index('</style>') + len('</style>')
head, body = src[:i], src[i:]

# 3) IMG 映射必须在主脚本之前求值
anchor = '<script>\n/* ---- data:'
assert anchor in body, 'main script anchor not found'
body = body.replace(anchor, '<script>window.__IMG=' + blob + ';</script>\n' + anchor, 1)

out = (
    '<!doctype html>\n<html lang="zh-CN">\n<head>\n'
    '<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    '<style>:root{color-scheme:light dark}html,body{margin:0}'
    'img{max-width:100%}[hidden]{display:none!important}</style>\n'
    + head +
    '\n</head>\n<body>\n' + body + '\n</body>\n</html>\n'
)
dst = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'typo_deck.html')
open(dst, 'w', encoding='utf-8').write(out)
print('%s  %.1f MB  (%d images inlined)' % (dst, len(out.encode('utf-8')) / 1e6, len(imgs)))
