/* 结果预览 · 预览切换（报告浏览 / 知识图谱浏览）
 * 运行时补丁：当前 dist 是在有 goai_final_lab 同级仓库的机器上构建的，这里无法重建；
 * 本脚本在「结果预览」页把预览区分成两个视图，源码版本见 src/views/ResultsView.vue（.preview-switch）。
 * 若页面已由重建后的源码渲染出 .preview-switch，本脚本不做任何事，可随该次重建一并删除。 */
(function () {
  'use strict';
  var KG_URL = 'knowledge/knowledge_layers.html?theme=console&autoplay=1';
  var CSS = '.preview-switch{display:inline-flex;border:1px solid var(--line,#D8DAD6);border-radius:8px;overflow:hidden;margin:0 0 10px;flex:none}'
    + '.preview-switch button{border:0;background:transparent;padding:4px 12px;font:inherit;font-size:13px;color:var(--slate,#66737B);cursor:pointer}'
    + '.preview-switch button.on{background:var(--verdigris-soft,#DDEBE7);color:var(--ink,#172B3A);font-weight:600}'
    + '.preview .kg-frame{display:block;width:100%;height:100%;border:0;background:#F5F3ED}'
    + '.preview-note{font-size:12px;line-height:18px;color:var(--slate,#66737B);margin:6px 2px 0}';
  function ensureStyle() {
    if (document.getElementById('preview-switch-style')) return;
    var st = document.createElement('style'); st.id = 'preview-switch-style'; st.textContent = CSS; document.head.appendChild(st);
  }
  function mount(detail) {
    if (detail.querySelector('.preview-switch')) return;   // already rendered (by the Vue source or a previous pass)
    var body = detail.querySelector('.d-body'); var preview = detail.querySelector('.preview'); if (!body || !preview) return;
    ensureStyle();
    var sw = document.createElement('div'); sw.className = 'preview-switch';
    var bReport = document.createElement('button'); bReport.textContent = '报告浏览'; bReport.className = 'on';
    var bGraph = document.createElement('button'); bGraph.textContent = '知识图谱浏览';
    sw.appendChild(bReport); sw.appendChild(bGraph);
    body.parentNode.insertBefore(sw, body);
    var frame = null, note = null;
    var original = Array.prototype.slice.call(preview.children);
    function show(mode) {
      bReport.className = mode === 'report' ? 'on' : ''; bGraph.className = mode === 'graph' ? 'on' : '';
      original.forEach(function (el) { el.style.display = mode === 'report' ? '' : 'none'; });
      if (mode === 'graph') {
        if (!frame) { frame = document.createElement('iframe'); frame.className = 'kg-frame'; frame.title = '知识图谱 · 逐层展开'; frame.src = KG_URL; preview.appendChild(frame); }
        frame.style.display = '';
        if (!note) { note = document.createElement('div'); note.className = 'preview-note'; note.textContent = '知识图谱：SAGE-Mat 知识森林（BYZSO 正式案例证据包，由 build_graph.py 确定性生成）。点卡片或圆点看出处与邻接；顶部台阶可跳级。'; preview.parentNode.insertBefore(note, preview.nextSibling); }
        note.style.display = '';
      } else { if (frame) frame.style.display = 'none'; if (note) note.style.display = 'none'; }
    }
    bReport.addEventListener('click', function () { show('report'); });
    bGraph.addEventListener('click', function () { show('graph'); });
    if (location.hash.indexOf('view=graph') >= 0) show('graph');
  }
  function scan() { document.querySelectorAll('.results-page .detail').forEach(mount); }
  var obs = new MutationObserver(function () { scan(); });
  function start() { scan(); obs.observe(document.body, { childList: true, subtree: true }); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
