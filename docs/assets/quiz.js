/* SC-200 刷題引擎
   模式（URL 可定址）：
     ?mode=domain&domain=D1&set=A&n=40   依領域（即時回饋）
     ?mode=random&n=50                   權重隨機（即時回饋）
     ?unit=P1-W2-2                       依單元（即時回饋）
     ?mode=mock&set=1                    模擬考（計時、交卷後對答案）
     ?mode=wrong                         錯題本重練
     ?mode=stats                         統計
   localStorage：sc200.wrong / sc200.stats / sc200.mock / sc200.lang
*/
(function () {
  'use strict';

  // 課程參數由同目錄的 quiz-config.json 提供，讓 SC-200 與 CISSP 共用同一支引擎。
  // 取不到設定時退回 SC-200 的預設值。
  var DOMAIN_ZH = { D1: '管理安全性作業環境', D2: '回應安全性事件', D3: '執行威脅搜捕' };
  var WEIGHTS = { D1: 0.43, D2: 0.36, D3: 0.21 };
  var MOCK_MINUTES = 100;
  var NS = 'sc200';                 // localStorage 命名空間（兩套課程各自獨立）
  var PASS_SCALED = 700;

  function applyConfig(cfg) {
    if (!cfg) return;
    if (cfg.domains) DOMAIN_ZH = cfg.domains;
    if (cfg.weights) WEIGHTS = cfg.weights;
    if (cfg.mock && cfg.mock.minutes) MOCK_MINUTES = cfg.mock.minutes;
    if (cfg.mock && cfg.mock.pass_scaled) PASS_SCALED = cfg.mock.pass_scaled;
    if (cfg.namespace) NS = cfg.namespace;
    if (cfg.modes) MODES = cfg.modes;
  }

  var BANK = { practice: [], mocks: {} };   // practice: d1+d2+d3 合併
  var state = null;                          // 當前 session
  var CFG = null;

  /* ---------- localStorage helpers ---------- */
  function lsGet(k, dflt) {
    try { return JSON.parse(localStorage.getItem(k)) || dflt; } catch (e) { return dflt; }
  }
  function lsSet(k, v) { localStorage.setItem(k, JSON.stringify(v)); }
  function getWrong() { return lsGet(NS + '.wrong', {}); }
  function getStats() { return lsGet(NS + '.stats', { attempts: [] }); }
  function getMock() { return lsGet(NS + '.mock', { results: [] }); }
  function getLang() { return localStorage.getItem(NS + '.lang') || 'both'; }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  /* ---------- 答題記錄 ---------- */
  function recordAttempt(q, ok, mode) {
    var st = getStats();
    st.attempts.push({ id: q.id, ok: ok, domain: q.domain, topic: q.topic || '', mode: mode, ts: Date.now() });
    if (st.attempts.length > 5000) st.attempts = st.attempts.slice(-5000);
    lsSet(NS + '.stats', st);
    var w = getWrong();
    if (ok) {
      if (w[q.id]) {
        w[q.id].streak = (w[q.id].streak || 0) + 1;
        if (w[q.id].streak >= 2) delete w[q.id];
      }
    } else {
      w[q.id] = { wrong: ((w[q.id] || {}).wrong || 0) + 1, streak: 0, ts: Date.now() };
    }
    lsSet(NS + '.wrong', w);
  }

  /* ---------- 題庫載入 ---------- */
  function loadBank() {
    return fetch('bank/index.json').then(function (r) {
      if (!r.ok) throw new Error('bank/index.json 載入失敗');
      return r.json();
    }).then(function (idx) {
      var jobs = [];
      (idx.practice_files || []).forEach(function (f) {
        jobs.push(fetch('bank/' + f).then(function (r) { return r.ok ? r.json() : []; })
          .then(function (qs) { BANK.practice = BANK.practice.concat(qs); }));
      });
      Object.keys(idx.mock_files || {}).forEach(function (setNo) {
        jobs.push(fetch('bank/' + idx.mock_files[setNo]).then(function (r) { return r.ok ? r.json() : []; })
          .then(function (qs) { BANK.mocks[setNo] = qs; }));
      });
      return Promise.all(jobs);
    });
  }

  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function pickWeightedRandom(n) {
    var byDom = { D1: [], D2: [], D3: [] };
    BANK.practice.forEach(function (q) { if (byDom[q.domain]) byDom[q.domain].push(q); });
    var out = [];
    Object.keys(WEIGHTS).forEach(function (d) {
      var take = Math.round(n * WEIGHTS[d]);
      out = out.concat(shuffle(byDom[d]).slice(0, take));
    });
    while (out.length < n && out.length < BANK.practice.length) {
      var extra = shuffle(BANK.practice).find(function (q) { return out.indexOf(q) < 0; });
      if (!extra) break;
      out.push(extra);
    }
    return shuffle(out).slice(0, n);
  }

  /* ---------- session 建立 ---------- */
  function buildSession(params) {
    var mode = params.get('mode') || (params.get('unit') ? 'unit' : 'home');
    var qs = [], title = '', timed = false;

    if (mode === 'domain') {
      var d = params.get('domain') || 'D1';
      var set = params.get('set');
      var n = parseInt(params.get('n') || '40', 10);
      qs = BANK.practice.filter(function (q) {
        return q.domain === d && (!set || q.set === set);
      });
      qs = shuffle(qs).slice(0, n);
      title = d + ' ' + (DOMAIN_ZH[d] || '') + (set ? '｜題組 ' + set : '') + '（' + qs.length + ' 題）';
    } else if (mode === 'random') {
      var n2 = parseInt(params.get('n') || '50', 10);
      qs = pickWeightedRandom(n2);
      title = '全領域權重混合（' + qs.length + ' 題）';
    } else if (mode === 'unit') {
      var unit = params.get('unit');
      qs = shuffle(BANK.practice.filter(function (q) { return q.unit === unit; }));
      title = '單元 ' + unit + '（' + qs.length + ' 題）';
    } else if (mode === 'mock') {
      var setNo = params.get('set') || '1';
      qs = (BANK.mocks[setNo] || []).slice();   // 模考固定順序
      title = '模擬考 ' + setNo + '（' + qs.length + ' 題／' + MOCK_MINUTES + ' 分鐘）';
      timed = true;
    } else if (mode === 'wrong') {
      var w = getWrong();
      var all = BANK.practice.slice();
      Object.keys(BANK.mocks).forEach(function (k) { all = all.concat(BANK.mocks[k]); });
      qs = shuffle(all.filter(function (q) { return w[q.id]; }));
      title = '錯題本重練（' + qs.length + ' 題）';
    }
    return { mode: mode, questions: qs, title: title, timed: timed,
             idx: 0, answers: {}, revealed: {}, startTs: Date.now(), timerId: null };
  }

  /* ---------- 視圖切換 ---------- */
  function show(view) {
    ['viewHome', 'viewQuiz', 'viewResult'].forEach(function (id) {
      document.getElementById(id).classList.toggle('hide', id !== view);
    });
  }

  /* ---------- 首頁 ---------- */
  var MODES = [
    { icon: '📚', title: '依領域練習', desc: '選領域即時回饋刷題', href: '?mode=domain&domain=D1&n=40' },
    { icon: '🎲', title: '權重隨機 50 題', desc: '依考試權重 43/36/21 抽樣', href: '?mode=random&n=50' },
    { icon: '⏱️', title: '模擬考', desc: '55 題／100 分鐘，交卷後對答案', href: '?mode=mock&set=1' },
    { icon: '📕', title: '錯題本', desc: '重練答錯的題目，連對 2 次移出', href: '?mode=wrong' },
    { icon: '📊', title: '學習統計', desc: '各領域正確率與最弱主題', href: '?mode=stats' },
    { icon: '🏠', title: '回儀表板', desc: '看今天該做什麼', href: 'index.html' }
  ];

  function renderHome() {
    var counts = { D1: 0, D2: 0, D3: 0 };
    BANK.practice.forEach(function (q) { if (counts[q.domain] != null) counts[q.domain]++; });
    var mockN = Object.keys(BANK.mocks).reduce(function (s, k) { return s + BANK.mocks[k].length; }, 0);
    document.getElementById('qSub').textContent =
      '練習庫 ' + BANK.practice.length + ' 題（D1 ' + counts.D1 + '／D2 ' + counts.D2 + '／D3 ' + counts.D3 +
      '）＋ 模擬考 ' + mockN + ' 題';
    var wrongN = Object.keys(getWrong()).length;

    document.getElementById('modeCards').innerHTML = MODES.map(function (m) {
      var extra = (m.title === '錯題本' && wrongN) ? '（現有 ' + wrongN + ' 題）' : '';
      return '<a class="mode-card" style="text-decoration:none;display:block" href="' + m.href + '">' +
        '<div class="m-icon">' + m.icon + '</div>' +
        '<div class="m-title">' + m.title + extra + '</div>' +
        '<div class="m-desc">' + m.desc + '</div></a>';
    }).join('');

    var lt = document.getElementById('langToggle');
    function refreshLang() {
      lt.textContent = '題幹語言：' + (getLang() === 'both' ? '中英對照' : '純英文（仿真）');
    }
    refreshLang();
    lt.onclick = function () {
      localStorage.setItem(NS + '.lang', getLang() === 'both' ? 'en' : 'both');
      refreshLang();
      if (state && state.questions.length) renderQuestion();
    };
    show('viewHome');
  }

  /* ---------- 作答 ---------- */
  function fmtTime(sec) {
    var m = Math.floor(sec / 60), s = sec % 60;
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  function startTimer() {
    var el = document.getElementById('qTimer');
    el.classList.remove('hide');
    var endTs = state.startTs + MOCK_MINUTES * 60 * 1000;
    state.timerId = setInterval(function () {
      var left = Math.max(0, Math.round((endTs - Date.now()) / 1000));
      el.textContent = '⏱ ' + fmtTime(left);
      el.classList.toggle('low', left < 600);
      if (left <= 0) { clearInterval(state.timerId); submitMock(true); }
    }, 500);
  }

  function isMulti(q) { return (q.answer || []).length > 1 || q.type === 'multi'; }

  function renderQuestion() {
    var q = state.questions[state.idx];
    if (!q) return;
    var lang = getLang();
    var practice = state.mode !== 'mock';
    var picked = state.answers[q.id] || [];
    var revealed = practice && state.revealed[q.id];

    document.getElementById('qPos').textContent = (state.idx + 1) + ' / ' + state.questions.length;
    document.getElementById('btnPrev').disabled = state.idx === 0;
    var last = state.idx === state.questions.length - 1;
    document.getElementById('btnNext').textContent = last ? '完成 ✓' : '下一題 →';

    var multi = isMulti(q);
    var html = '<div class="q-meta-line">' + esc(q.id) + ' · ' + esc(q.domain) + ' ' +
      esc(DOMAIN_ZH[q.domain] || '') + (q.topic ? ' · ' + esc(q.topic) : '') +
      (multi ? ' · <strong>複選題</strong>' : '') +
      ((q.tags || []).indexOf('2026') >= 0 ? ' · <span class="badge-2026">2026 新考點</span>' : '') + '</div>';
    html += '<div class="q-stem">' + esc(q.stem_en) + '</div>';
    if (lang === 'both') html += '<div class="q-zh">' + esc(q.stem_zh) + '</div>';

    q.options.forEach(function (o) {
      var cls = 'q-opt-btn';
      var sel = picked.indexOf(o.key) >= 0;
      if (revealed) {
        if ((q.answer || []).indexOf(o.key) >= 0) cls += ' correct';
        else if (sel) cls += ' wrong';
      } else if (sel) cls += ' sel';
      html += '<button type="button" class="' + cls + '" data-key="' + o.key + '">' +
        '<span class="ok-key">' + o.key + '</span><span>' + esc(o.text_en) +
        (lang === 'both' ? '<br><span style="font-size:12.5px;color:var(--muted)">' + esc(o.text_zh) + '</span>' : '') +
        '</span></button>';
    });

    if (practice && multi && !revealed) {
      html += '<button type="button" class="qbtn primary" id="btnCheckMulti" style="margin-top:8px">送出答案</button>';
    }

    if (revealed) {
      var ok = sameAnswer(picked, q.answer);
      html += '<div class="q-explain">' +
        '<div class="' + (ok ? 'verdict-ok' : 'verdict-no') + '">' +
        (ok ? '✓ 答對了' : '✗ 答錯了（正解：' + (q.answer || []).join('、') + '）') + '</div>' +
        '<p>' + esc(q.explanation_zh) + '</p>';
      var ww = q.why_wrong_zh || {};
      var wrongKeys = Object.keys(ww);
      if (wrongKeys.length) {
        html += '<ul>' + wrongKeys.map(function (k) {
          return '<li><strong>' + k + '</strong>：' + esc(ww[k]) + '</li>';
        }).join('') + '</ul>';
      }
      if (q.ms_learn_ref) {
        html += '<p style="font-size:12.5px"><a href="' + esc(q.ms_learn_ref) + '" target="_blank" rel="noopener">📚 MS Learn 參考 ↗</a></p>';
      }
      html += '</div>';
    }

    document.getElementById('qBody').innerHTML = html;

    document.querySelectorAll('#qBody .q-opt-btn').forEach(function (btn) {
      btn.addEventListener('click', function () { onPick(q, btn.dataset.key); });
    });
    var cm = document.getElementById('btnCheckMulti');
    if (cm) cm.addEventListener('click', function () { reveal(q); });
  }

  function sameAnswer(picked, ans) {
    if (!picked || !ans) return false;
    if (picked.length !== ans.length) return false;
    var a = picked.slice().sort().join(''), b = ans.slice().sort().join('');
    return a === b;
  }

  function onPick(q, key) {
    var practice = state.mode !== 'mock';
    var multi = isMulti(q);
    if (practice && state.revealed[q.id]) return;   // 已對答案，不能改
    var cur = state.answers[q.id] || [];
    if (multi) {
      var i = cur.indexOf(key);
      if (i >= 0) cur.splice(i, 1); else cur.push(key);
      state.answers[q.id] = cur;
      if (state.mode === 'mock') { renderQuestion(); return; }
      renderQuestion();
    } else {
      state.answers[q.id] = [key];
      if (practice) reveal(q); else { renderQuestion(); }
    }
  }

  function reveal(q) {
    state.revealed[q.id] = true;
    var ok = sameAnswer(state.answers[q.id] || [], q.answer);
    recordAttempt(q, ok, state.mode);
    renderQuestion();
  }

  function next() {
    var last = state.idx === state.questions.length - 1;
    if (last) {
      if (state.mode === 'mock') submitMock(false);
      else finishPractice();
    } else {
      state.idx++;
      renderQuestion();
    }
  }

  /* ---------- 練習結束 ---------- */
  function finishPractice() {
    var qs = state.questions;
    var answered = qs.filter(function (q) { return state.revealed[q.id]; });
    var correct = answered.filter(function (q) { return sameAnswer(state.answers[q.id] || [], q.answer); });
    var pct = answered.length ? Math.round(correct.length / answered.length * 100) : 0;
    var html = '<div class="masthead" style="margin-bottom:14px"><div class="kicker">練習結果</div>' +
      '<h1>' + esc(state.title) + '</h1></div>' +
      '<div class="result-grid">' +
      tile(answered.length, '已作答') + tile(correct.length, '答對') +
      tile(pct + '%', '正確率', pct >= 70 ? 'pass' : 'fail') +
      tile(Object.keys(getWrong()).length, '錯題本題數') + '</div>' +
      '<div class="controls">' +
      '<a class="qbtn primary" style="text-decoration:none" href="quiz.html">回刷題首頁</a>' +
      '<a class="qbtn" style="text-decoration:none" href="?mode=wrong">練錯題本</a>' +
      '<a class="qbtn" style="text-decoration:none" href="index.html">回儀表板</a></div>';
    document.getElementById('viewResult').innerHTML = html;
    show('viewResult');
  }

  function tile(num, lbl, cls) {
    return '<div class="stat-tile ' + (cls || '') + '"><div class="st-num">' + num +
      '</div><div class="st-lbl">' + lbl + '</div></div>';
  }

  /* ---------- 模考交卷 ---------- */
  function submitMock(timeout) {
    if (state.timerId) clearInterval(state.timerId);
    var qs = state.questions;
    var perDom = {};
    var correctN = 0;
    qs.forEach(function (q) {
      var ok = sameAnswer(state.answers[q.id] || [], q.answer);
      recordAttempt(q, ok, 'mock');
      if (ok) correctN++;
      perDom[q.domain] = perDom[q.domain] || { total: 0, ok: 0 };
      perDom[q.domain].total++;
      if (ok) perDom[q.domain].ok++;
    });
    var pct = qs.length ? Math.round(correctN / qs.length * 100) : 0;
    var scaled = Math.round(pct * 10);   // 近似量尺：% × 10
    var pass = scaled >= PASS_SCALED;
    var usedMin = Math.round((Date.now() - state.startTs) / 60000);

    var mk = getMock();
    var params = new URLSearchParams(location.search);
    mk.results.push({ set: params.get('set') || '1', pct: pct, scaled: scaled,
      perDomain: perDom, minutes: usedMin, ts: Date.now() });
    lsSet(NS + '.mock', mk);

    var html = '<div class="masthead" style="margin-bottom:14px"><div class="kicker">模擬考結果' +
      (timeout ? '（時間到自動交卷）' : '') + '</div><h1>' + esc(state.title) + '</h1></div>';
    html += '<div class="result-grid">' +
      tile(scaled, '量尺分數（及格 ' + PASS_SCALED + '）', pass ? 'pass' : 'fail') +
      tile(correctN + ' / ' + qs.length, '答對題數') +
      tile(pct + '%', '正確率', pct >= 70 ? 'pass' : 'fail') +
      tile(usedMin + ' 分', '作答時間') + '</div>';
    html += '<div class="card-block"><strong>各領域表現</strong>';
    Object.keys(perDom).sort().forEach(function (d) {
      var p = perDom[d], dp = Math.round(p.ok / p.total * 100);
      html += '<div class="dom-bar-row"><span class="db-label">' + d + ' ' + esc(DOMAIN_ZH[d] || '') +
        '</span><div class="dom-bar"><div style="width:' + dp + '%"></div></div>' +
        '<span class="db-num">' + p.ok + '/' + p.total + '（' + dp + '%）</span></div>';
    });
    html += '</div>';

    html += '<div class="eyebrow">全卷檢討</div>';
    qs.forEach(function (q, i) {
      var picked = state.answers[q.id] || [];
      var ok = sameAnswer(picked, q.answer);
      html += '<div class="q-card"><div class="q-eyebrow">QUESTION ' + (i + 1) +
        ' · ' + (ok ? '<span style="color:var(--ok)">✓</span>' : '<span style="color:#C0392B">✗</span>') + '</div>' +
        '<div class="q-stem">' + esc(q.stem_en) + '</div>' +
        '<div class="q-zh">' + esc(q.stem_zh) + '</div>';
      q.options.forEach(function (o) {
        var mark = (q.answer || []).indexOf(o.key) >= 0 ? ' ✓' :
          (picked.indexOf(o.key) >= 0 ? ' ←你的答案' : '');
        var style = (q.answer || []).indexOf(o.key) >= 0 ? 'border-color:var(--ok)' :
          (picked.indexOf(o.key) >= 0 && !ok ? 'border-color:#C0392B' : '');
        html += '<div class="q-opt" style="' + style + '"><strong>' + o.key + '.</strong> ' +
          esc(o.text_en) + '<span style="color:var(--muted);font-size:12px">' + mark + '</span></div>';
      });
      html += '<div class="q-ans"><span class="correct">正解：' + (q.answer || []).join('、') + '</span> — ' +
        esc(q.explanation_zh) + '</div></div>';
    });
    html += '<div class="controls"><a class="qbtn primary" style="text-decoration:none" href="quiz.html">回刷題首頁</a>' +
      '<a class="qbtn" style="text-decoration:none" href="?mode=wrong">練錯題本</a></div>';

    document.getElementById('viewResult').innerHTML = html;
    show('viewResult');
    window.scrollTo(0, 0);
  }

  /* ---------- 統計 ---------- */
  function renderStats() {
    var st = getStats(), mk = getMock();
    var byDom = {}, byTopic = {};
    st.attempts.forEach(function (a) {
      byDom[a.domain] = byDom[a.domain] || { total: 0, ok: 0 };
      byDom[a.domain].total++; if (a.ok) byDom[a.domain].ok++;
      if (a.topic) {
        byTopic[a.domain + '/' + a.topic] = byTopic[a.domain + '/' + a.topic] || { total: 0, ok: 0 };
        byTopic[a.domain + '/' + a.topic].total++; if (a.ok) byTopic[a.domain + '/' + a.topic].ok++;
      }
    });
    var html = '<div class="masthead" style="margin-bottom:14px"><div class="kicker">學習統計</div>' +
      '<h1>刷題數據</h1><p class="sub">共作答 ' + st.attempts.length + ' 次 · 錯題本現有 ' +
      Object.keys(getWrong()).length + ' 題</p></div>';

    html += '<div class="card-block"><strong>各領域正確率</strong>';
    ['D1', 'D2', 'D3'].forEach(function (d) {
      var p = byDom[d];
      if (!p) { html += '<div class="dom-bar-row"><span class="db-label">' + d + ' ' + DOMAIN_ZH[d] +
        '</span><div class="dom-bar"><div style="width:0"></div></div><span class="db-num">尚無</span></div>'; return; }
      var dp = Math.round(p.ok / p.total * 100);
      html += '<div class="dom-bar-row"><span class="db-label">' + d + ' ' + DOMAIN_ZH[d] +
        '</span><div class="dom-bar"><div style="width:' + dp + '%"></div></div>' +
        '<span class="db-num">' + p.ok + '/' + p.total + '（' + dp + '%）</span></div>';
    });
    html += '</div>';

    var weakest = Object.keys(byTopic).map(function (k) {
      var p = byTopic[k];
      return { k: k, pct: Math.round(p.ok / p.total * 100), n: p.total };
    }).filter(function (t) { return t.n >= 3; }).sort(function (a, b) { return a.pct - b.pct; }).slice(0, 8);
    if (weakest.length) {
      html += '<div class="card-block"><strong>最弱主題（作答 ≥3 次）</strong><ul>' +
        weakest.map(function (t) {
          return '<li><code>' + esc(t.k) + '</code>：' + t.pct + '%（' + t.n + ' 次）</li>';
        }).join('') + '</ul>' +
        '<p style="font-size:13px">👉 弱項加強日建議：挑最弱領域 <a href="?mode=domain&domain=' +
        (weakest[0] ? weakest[0].k.split('/')[0] : 'D1') + '&n=40">重練 40 題 →</a></p></div>';
    }

    if (mk.results.length) {
      html += '<div class="card-block"><strong>模擬考歷史</strong><div class="tbl-scroll"><table class="data"><thead><tr>' +
        '<th>日期</th><th>模考</th><th>量尺分數</th><th>正確率</th><th>用時</th></tr></thead><tbody>' +
        mk.results.map(function (r) {
          var d = new Date(r.ts).toLocaleDateString('zh-TW');
          var color = r.scaled >= 700 ? 'var(--ok)' : '#C0392B';
          return '<tr><td>' + d + '</td><td>模擬考 ' + esc(r.set) + '</td>' +
            '<td style="color:' + color + ';font-weight:700">' + r.scaled + '</td>' +
            '<td>' + r.pct + '%</td><td>' + r.minutes + ' 分</td></tr>';
        }).join('') + '</tbody></table></div></div>';
    }

    html += '<div class="controls"><a class="qbtn primary" style="text-decoration:none" href="quiz.html">回刷題首頁</a></div>';
    document.getElementById('viewResult').innerHTML = html;
    show('viewResult');
  }

  /* ---------- 啟動 ---------- */
  function startSession(params) {
    state = buildSession(params);
    if (!state.questions.length) {
      document.getElementById('qSub').textContent = '這個條件下沒有題目（題庫可能還在建置中）。';
      renderHome();
      return;
    }
    document.getElementById('qTitle').textContent = state.title;
    document.getElementById('qSub').textContent = state.mode === 'mock'
      ? '計時開始！交卷前不會顯示對錯。中途離開視同放棄。'
      : '點選選項立即對答案；答錯會進錯題本。';
    document.getElementById('btnSubmitMock').classList.toggle('hide', state.mode !== 'mock');
    show('viewQuiz');
    if (state.timed) startTimer();
    renderQuestion();
  }

  document.getElementById('btnPrev').addEventListener('click', function () {
    if (state.idx > 0) { state.idx--; renderQuestion(); }
  });
  document.getElementById('btnNext').addEventListener('click', next);
  document.getElementById('btnQuit').addEventListener('click', function () {
    if (state && state.mode === 'mock') {
      if (!confirm('模考中離開將直接交卷計分，確定？')) return;
      submitMock(false); return;
    }
    if (state) finishPractice();
  });
  document.getElementById('btnSubmitMock').addEventListener('click', function () {
    if (confirm('確定要交卷？')) submitMock(false);
  });

  document.addEventListener('keydown', function (e) {
    if (!state || document.getElementById('viewQuiz').classList.contains('hide')) return;
    var k = e.key.toUpperCase();
    if (['A', 'B', 'C', 'D', 'E'].indexOf(k) >= 0) {
      var q = state.questions[state.idx];
      if (q && q.options.some(function (o) { return o.key === k; })) onPick(q, k);
    } else if (e.key === 'Enter') { next(); }
    else if (e.key === 'ArrowLeft' && state.idx > 0) { state.idx--; renderQuestion(); }
    else if (e.key === 'ArrowRight') { if (state.idx < state.questions.length - 1) { state.idx++; renderQuestion(); } }
  });

  fetch('schedule.json').then(function (r) { return r.json(); }).then(function (s) { CFG = s; }).catch(function () {});

  fetch('quiz-config.json')
    .then(function (r) { return r.ok ? r.json() : null; })
    .catch(function () { return null; })
    .then(applyConfig)
    .then(loadBank).then(function () {
    var params = new URLSearchParams(location.search);
    var mode = params.get('mode') || (params.get('unit') ? 'unit' : 'home');
    if (mode === 'home') renderHome();
    else if (mode === 'stats') renderStats();
    else startSession(params);
  }).catch(function (e) {
    document.getElementById('qSub').textContent = '題庫載入失敗：' + e.message;
  });
})();
