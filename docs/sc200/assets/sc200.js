/* SC-200 共用前端：KQL 語法上色、TOC、複製按鈕、完成進度（localStorage） */
(function () {
  'use strict';

  /* ---------- KQL 語法上色（零依賴 regex highlighter） ---------- */
  var KQL_KEYWORDS = [
    'let', 'where', 'project', 'project-away', 'project-rename', 'extend', 'summarize',
    'join', 'union', 'parse', 'parse-where', 'order', 'sort', 'by', 'asc', 'desc',
    'take', 'limit', 'top', 'distinct', 'count', 'render', 'evaluate', 'invoke',
    'mv-expand', 'mv-apply', 'make-series', 'range', 'datatable', 'externaldata',
    'on', 'kind', 'inner', 'leftouter', 'rightouter', 'fullouter', 'innerunique',
    'leftsemi', 'leftanti', 'has', 'has_any', 'has_all', 'contains', 'startswith',
    'endswith', 'matches', 'regex', 'in', 'and', 'or', 'not', 'between', 'ago',
    'now', 'true', 'false', 'case', 'iff', 'isempty', 'isnotempty', 'isnull', 'isnotnull'
  ];
  var KQL_FUNCS = [
    'bin', 'count', 'countif', 'dcount', 'sum', 'sumif', 'avg', 'min', 'max',
    'arg_max', 'arg_min', 'make_list', 'make_set', 'strcat', 'split', 'tostring',
    'toint', 'tolong', 'todatetime', 'totimespan', 'tolower', 'toupper', 'substring',
    'extract', 'extract_all', 'parse_json', 'todynamic', 'format_datetime',
    'datetime_diff', 'startofday', 'endofday', 'percentile', 'series_decompose_anomalies',
    'ipv4_is_in_range', 'geo_ip_lookup', 'base64_decode_tostring', 'hash_sha256'
  ];
  var kw = new RegExp('\\b(' + KQL_KEYWORDS.join('|').replace(/-/g, '\\-') + ')\\b', 'g');
  var fn = new RegExp('\\b(' + KQL_FUNCS.join('|') + ')(?=\\s*\\()', 'g');

  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function highlightKql(src) {
    var out = [];
    // 逐行處理：註解 // 到行尾；字串 '..' ".." 先抽出避免誤染
    src.split('\n').forEach(function (line) {
      var cIdx = line.indexOf('//');
      var code = cIdx >= 0 ? line.slice(0, cIdx) : line;
      var comment = cIdx >= 0 ? line.slice(cIdx) : '';
      var tokens = [];
      var rest = code;
      var m;
      var strRe = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/;
      while ((m = rest.match(strRe))) {
        tokens.push({ t: 'code', v: rest.slice(0, m.index) });
        tokens.push({ t: 'str', v: m[1] });
        rest = rest.slice(m.index + m[1].length);
      }
      tokens.push({ t: 'code', v: rest });
      var html = tokens.map(function (tk) {
        if (tk.t === 'str') return '<span class="s">' + esc(tk.v) + '</span>';
        return esc(tk.v)
          .replace(kw, '<span class="k">$1</span>')
          .replace(fn, '<span class="f">$1</span>')
          .replace(/\b(\d+(?:\.\d+)?[dhms]?)\b/g, '<span class="n">$1</span>');
      }).join('');
      if (comment) html += '<span class="c">' + esc(comment) + '</span>';
      out.push(html);
    });
    return out.join('\n');
  }

  function initKql() {
    document.querySelectorAll('pre.kql').forEach(function (pre) {
      var raw = pre.textContent;
      pre.innerHTML = highlightKql(raw);
      var wrap = pre.parentElement;
      if (!wrap.classList.contains('kql-block')) {
        var w = document.createElement('div');
        w.className = 'kql-block';
        pre.replaceWith(w);
        w.appendChild(pre);
        wrap = w;
      }
      var btn = document.createElement('button');
      btn.className = 'kql-copy';
      btn.type = 'button';
      btn.textContent = '複製';
      btn.addEventListener('click', function () {
        navigator.clipboard.writeText(raw).then(function () {
          btn.textContent = '已複製 ✓';
          setTimeout(function () { btn.textContent = '複製'; }, 1500);
        });
      });
      wrap.appendChild(btn);
    });
  }

  /* ---------- TOC（由 h2[data-toc] 自動生成，≥1100px 顯示） ---------- */
  function initToc() {
    var heads = document.querySelectorAll('article h2[data-toc]');
    if (!heads.length) return;
    document.body.classList.add('has-toc');
    var toc = document.createElement('nav');
    toc.className = 'toc';
    toc.innerHTML = '<div class="toc-label">本頁目錄</div>';
    heads.forEach(function (h, i) {
      if (!h.id) h.id = 'sec-' + (i + 1);
      var a = document.createElement('a');
      a.href = '#' + h.id;
      a.textContent = h.getAttribute('data-toc') || h.textContent;
      toc.appendChild(a);
    });
    document.querySelector('.wrap').appendChild(toc);
    var links = toc.querySelectorAll('a');
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          links.forEach(function (l) {
            l.classList.toggle('active', l.getAttribute('href') === '#' + e.target.id);
          });
        }
      });
    }, { rootMargin: '0px 0px -75% 0px' });
    heads.forEach(function (h) { obs.observe(h); });
  }

  /* ---------- 完成進度（localStorage: sc200.progress = {seq: true}） ---------- */
  var PKEY = 'sc200.progress';
  function getProgress() {
    try { return JSON.parse(localStorage.getItem(PKEY)) || {}; } catch (e) { return {}; }
  }
  function setProgress(p) { localStorage.setItem(PKEY, JSON.stringify(p)); }

  function initDoneRow() {
    var row = document.querySelector('.done-row input[data-seq]');
    if (!row) return;
    var seq = row.getAttribute('data-seq');
    var p = getProgress();
    row.checked = !!p[seq];
    row.addEventListener('change', function () {
      var cur = getProgress();
      if (row.checked) cur[seq] = true; else delete cur[seq];
      setProgress(cur);
    });
  }

  window.SC200 = { getProgress: getProgress, setProgress: setProgress, highlightKql: highlightKql };

  document.addEventListener('DOMContentLoaded', function () {
    initKql();
    initToc();
    initDoneRow();
  });
})();
