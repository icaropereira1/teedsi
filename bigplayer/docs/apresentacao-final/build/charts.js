// Gráficos em SVG, desenhados a partir dos CSVs do projeto (ver build.sh).
// Padrão visual das apresentações anteriores (notebooks/12_graficos_apresentacao.py).
const C = {
  surface: '#F1EEE9', ink: '#1A1A1A', ink2: '#5C5852', grid: '#DAD5CD',
  purple: '#7B57C8', orange: '#F0A030', orangeTxt: '#B86A00', mint: '#BCECE6',
  pink: '#E06388', muted: '#8E887F', band: '#E4DFD7',
};

// ---------- utilidades ----------
function parseCSV(txt) {
  const lines = txt.trim().split('\n');
  const head = lines[0].split(',');
  return lines.slice(1).map(l => {
    const v = l.split(','); const o = {};
    head.forEach((h, i) => { const x = v[i]; o[h] = (x !== '' && !isNaN(+x)) ? +x : x; });
    return o;
  });
}
const D = {}; for (const k in CSV) D[k] = parseCSV(CSV[k]);

function br(x, dec = 1, plus = false) {
  if (Math.abs(x) < 1e-9) x = 0;
  const s = Math.abs(x).toLocaleString('pt-BR', { minimumFractionDigits: dec, maximumFractionDigits: dec });
  const r = +x.toFixed(dec);
  if (r < 0) return '−' + s;
  if (plus && r > 0) return '+' + s;
  return s;
}
const lin = (d0, d1, r0, r1) => v => r0 + (v - d0) / (d1 - d0) * (r1 - r0);
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
function T(x, y, s, o = {}) {
  const a = Object.assign({ size: 13, fill: C.ink, anchor: 'start', weight: 400 }, o);
  return `<text x="${x}" y="${y}" font-size="${a.size}" fill="${a.fill}" text-anchor="${a.anchor}" font-weight="${a.weight}"${a.rot ? ` transform="rotate(${a.rot} ${x} ${y})"` : ''}${a.italic ? ' font-style="italic"' : ''}>${esc(s)}</text>`;
}
const L = (x1, y1, x2, y2, st = C.grid, w = 1, dash = '') => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${st}" stroke-width="${w}"${dash ? ` stroke-dasharray="${dash}"` : ''}/>`;
const R = (x, y, w, h, f, o = '') => `<rect x="${x}" y="${y}" width="${Math.max(0, w)}" height="${Math.max(0, h)}" fill="${f}" ${o}/>`;
const Ci = (x, y, r, f, st = C.ink, sw = 1) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${f}" stroke="${st}" stroke-width="${sw}"/>`;
const P = (pts, st, w = 2.5, dash = '') => `<polyline points="${pts.map(p => p.join(',')).join(' ')}" fill="none" stroke="${st}" stroke-width="${w}" stroke-linejoin="round"${dash ? ` stroke-dasharray="${dash}"` : ''}/>`;
const svg = (w, h, inner) => `<svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Arial, sans-serif">${inner}</svg>`;

// legenda horizontal: itens {kind:'line'|'dash'|'dot'|'rect'|'band'|'err', color, label}
function legend(x, y, items, gap = 26) {
  let s = '', cx = x;
  for (const it of items) {
    if (it.kind === 'line') s += L(cx, y - 4, cx + 22, y - 4, it.color, 3);
    if (it.kind === 'dash') s += L(cx, y - 4, cx + 22, y - 4, it.color, 2.2, '5 3');
    if (it.kind === 'dot') s += Ci(cx + 11, y - 4, 5.5, it.color);
    if (it.kind === 'rect') s += R(cx + 2, y - 11, 18, 13, it.color, it.extra || '');
    if (it.kind === 'band') s += R(cx, y - 11, 22, 13, it.color);
    if (it.kind === 'err') s += L(cx + 11, y - 12, cx + 11, y + 4, C.ink, 1.3) + Ci(cx + 11, y - 4, 5, it.color);
    if (it.kind === 'tick') s += L(cx + 3, y - 4, cx + 19, y - 4, it.color, 3.5);
    s += T(cx + 28, y, it.label, { size: 12.5, fill: C.ink });
    cx += 28 + it.label.length * 6.6 + gap;
  }
  return s;
}
const HORAS = ['09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30'];
const hLabel = h => h.replace(/^0/, '').replace(':00', 'h').replace(':', 'h');

// ================= Slide 2: cobertura dos dados =================
function chartCobertura() {
  const W = 800, H = 430, x0 = 70, x1 = 780;
  const d0 = new Date('2020-07-01'), d1 = new Date('2026-12-31');
  const sx = v => lin(+d0, +d1, x0, x1)(+new Date(v));
  let s = '';
  // anos
  for (let y = 2021; y <= 2026; y++) {
    const x = sx(`${y}-01-01`);
    s += L(x, 60, x, 330, C.grid, 1) + T(x, 352, y, { anchor: 'middle', size: 13, fill: C.ink2 });
  }
  s += L(x0, 330, x1, 330, C.ink, 1.1);
  const rows = [
    { k: 'wdo', name: 'WDO', sub: 'mini dólar', color: C.purple, y: 95 },
    { k: 'win', name: 'WIN', sub: 'mini índice', color: C.orange, y: 225 },
  ];
  for (const r of rows) {
    const m = MANIFEST[r.k], bh = 46;
    const ex0 = sx(m.exploration.start), ho0 = sx(m.holdout_start), ho1 = sx(m.holdout.end);
    s += T(10, r.y - 22, `${r.name} · ${r.sub}`, { size: 15, weight: 700 });
    s += R(ex0, r.y, ho0 - ex0, bh, r.color, 'rx="3"');
    s += R(ho0, r.y, ho1 - ho0, bh, 'url(#hatch)', `rx="3" stroke="${C.ink2}" stroke-width="1"`);
    for (const b of D['bur_' + r.k]) {
      const bx = sx(b.start), bw = Math.max(3, sx(b.end) - bx);
      s += R(bx, r.y - 4, bw, bh + 8, C.pink, 'rx="2"');
    }
    s += T(ex0 + 10, r.y + 20, `exploração · ${m.exploration.days.toLocaleString('pt-BR')} pregões`, { size: 13, fill: '#fff', weight: 700 });
    s += T(ex0 + 10, r.y + 37, `${m.exploration.rows.toLocaleString('pt-BR')} candles de 1 min`, { size: 12, fill: '#fff' });
    s += T(ho0 + (ho1 - ho0) / 2, r.y + bh + 18, `hold-out: ${m.holdout.days} pregões (trancado)`, { size: 12, anchor: 'middle', fill: C.ink2 });
    const big = D['bur_' + r.k].reduce((a, b) => (b.trading_days > a.trading_days ? b : a));
    const bx = sx(big.start) + (sx(big.end) - sx(big.start)) / 2;
    s += T(bx, r.y - 10, `buraco: ${big.trading_days} pregões`, { size: 12, anchor: 'middle', fill: '#B03A5F', weight: 700 });
  }
  const leg = legend(x0, 400, [
    { kind: 'rect', color: C.purple, label: 'exploração WDO' },
    { kind: 'rect', color: C.orange, label: 'exploração WIN' },
    { kind: 'rect', color: 'url(#hatch)', label: 'hold-out (últimos 12 meses)', extra: `stroke="${C.ink2}"` },
    { kind: 'rect', color: C.pink, label: 'buraco nos dados' },
  ], 18);
  const defs = `<defs><pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="7" height="7" fill="#E9E4DC"/><line x1="0" y1="0" x2="0" y2="7" stroke="${C.muted}" stroke-width="2"/></pattern></defs>`;
  return svg(W, H, defs + s + leg);
}

// ================= Slide 3: Gate 1 (forest plot) =================
function chartGate1() {
  const W = 800, H = 470, x0 = 300, x1 = 690, top = 30, rowH = 27;
  const nome = {
    E1: 'E1 · volume anômalo (z ≥ 3)', E2: 'E2 · volume + lote grande', E3: 'E3 · volume alto por 5 min',
    P1: 'P1 · fluxo persistente', X1: 'X1 · pressão no extremo', A1: 'A1 · pausa com volume',
  };
  const pick = (rows, ev) => rows.find(r => r.evento === ev && r.h_min === 15);
  const rows = [
    { g: 'WDO · rodada 1', ...pick(D.ev_wdo, 'E1'), c: C.purple }, { ...pick(D.ev_wdo, 'E2'), c: C.purple }, { ...pick(D.ev_wdo, 'E3'), c: C.purple },
    { g: 'WDO · rodada 2', ...pick(D.ev_r2, 'P1'), c: C.purple }, { ...pick(D.ev_r2, 'X1'), c: C.purple }, { ...pick(D.ev_r2, 'A1'), c: C.purple, hl: 1 },
    { g: 'WIN · rodada 1', ...pick(D.ev_win, 'E1'), c: C.orange }, { ...pick(D.ev_win, 'E2'), c: C.orange }, { ...pick(D.ev_win, 'E3'), c: C.orange },
    { g: 'WIN · confirmação', ...pick(D.ev_conf, 'A1'), c: C.orange, hl: 1 },
  ];
  const sx = lin(-4, 3, x0, x1);
  let s = '', y = top;
  const yEnd = top + rows.length * rowH + 4 * 20;
  for (let v = -4; v <= 3; v++) {
    s += L(sx(v), top - 6, sx(v), yEnd, v === 0 ? C.ink : C.grid, v === 0 ? 1.4 : 1);
    s += T(sx(v), yEnd + 20, br(v, 0, true), { anchor: 'middle', size: 12.5, fill: C.ink2 });
  }
  s += T((x0 + x1) / 2, yEnd + 42, 'efeito em 15 min (bps): retorno na direção do evento − controle', { anchor: 'middle', size: 12.5, fill: C.ink2 });
  s += T(x1 + 52, top - 14, 'p-valor', { anchor: 'middle', size: 12, fill: C.ink2, weight: 700 });
  for (const r of rows) {
    if (r.g) { y += 20; s += T(10, y - 5, r.g, { size: 12.5, weight: 700, fill: r.c === C.purple ? C.purple : C.orangeTxt }); }
    const cy = y + rowH / 2;
    if (r.hl) s += R(4, y + 2, x1 + 100, rowH - 4, C.mint, 'rx="5" opacity="0.65"');
    s += T(24, cy + 4, nome[r.evento], { size: 12.5 });
    s += L(sx(r.ic95_inf), cy, sx(r.ic95_sup), cy, C.ink, 1.6);
    s += L(sx(r.ic95_inf), cy - 5, sx(r.ic95_inf), cy + 5, C.ink, 1.6) + L(sx(r.ic95_sup), cy - 5, sx(r.ic95_sup), cy + 5, C.ink, 1.6);
    s += Ci(sx(r.efeito_bps), cy, 6.5, r.c);
    s += T(x1 + 52, cy + 4, br(r.p, r.p < 0.1 ? 3 : 2), { anchor: 'middle', size: 12.5, weight: r.hl ? 700 : 400 });
    y += rowH;
  }
  s += legend(24, H - 4, [
    { kind: 'err', color: C.purple, label: 'WDO: efeito e IC 95%' },
    { kind: 'err', color: C.orange, label: 'WIN: efeito e IC 95%' },
    { kind: 'band', color: C.mint, label: 'A1: candidato que não se confirmou' },
  ], 18);
  return svg(W, H, s);
}

// ================= Slide 4: o minuto do pico =================
function chartMinutoPico() {
  const W = 1180, H = 380, x0 = 80, x1 = 1160;
  const pw = D.picos_wdo, pn = D.picos_win;
  const step = (x1 - x0) / HORAS.length, cx = i => x0 + step * (i + 0.5);
  let s = '';
  // painel A: volume x tarde
  const aT = 58, aB = 162, sa = lin(0, 4.5, aB, aT);
  s += T(x0 - 70, 46, 'A · volume no minuto do pico ÷ volume típico da tarde (1 = normal da tarde)', { size: 13.5, weight: 700 });
  for (const v of [0, 1, 2, 3, 4]) { s += L(x0, sa(v), x1, sa(v), v === 0 ? C.ink : C.grid) + T(x0 - 10, sa(v) + 4, v + '×', { anchor: 'end', size: 12, fill: C.ink2 }); }
  s += L(x0, sa(1), x1, sa(1), C.ink2, 1.3, '5 4');
  HORAS.forEach((h, i) => {
    const a = pw.find(r => r.horario === h), b = pn.find(r => r.horario === h), bw = step * 0.32;
    s += R(cx(i) - bw - 1, sa(a.volume_x_tarde), bw, aB - sa(a.volume_x_tarde), C.purple);
    s += R(cx(i) + 1, sa(b.volume_x_tarde), bw, aB - sa(b.volume_x_tarde), C.orange);
  });
  // painel B: % mexeu mais
  const bT = 204, bB = 350, sb = lin(44, 68, bB, bT);
  s += T(x0 - 70, 190, 'B · % dos pregões em que o preço andou mais no minuto do pico (T) que no minuto antes (T−1)', { size: 13.5, weight: 700 });
  s += R(x0, sb(53), x1 - x0, sb(47) - sb(53), C.band);
  for (const v of [45, 50, 55, 60, 65]) { s += L(x0, sb(v), x1, sb(v), v === 50 ? C.ink2 : C.grid, v === 50 ? 1.3 : 1, v === 50 ? '5 4' : '') + T(x0 - 10, sb(v) + 4, v + '%', { anchor: 'end', size: 12, fill: C.ink2 }); }
  s += T(x1 - 6, sb(47) - 5, 'faixa de acaso: 50% ± 3 p.p.', { anchor: 'end', size: 11.5, fill: C.ink2, italic: 1 });
  for (const [rows, col, dx] of [[pw, C.purple, -5], [pn, C.orange, 5]]) {
    const pts = HORAS.map((h, i) => [cx(i) + dx, sb(rows.find(r => r.horario === h).pico_maior_pct)]);
    s += P(pts, col, 2, '');
    pts.forEach(p => { s += Ci(p[0], p[1], 5, col); });
  }
  const top = pn.find(r => r.horario === '10:00');
  s += T(cx(1) + 12, sb(top.pico_maior_pct) - 6, `WIN 10h: ${br(top.pico_maior_pct, 1)}%`, { size: 12, weight: 700, fill: C.orangeTxt });
  HORAS.forEach((h, i) => { s += T(cx(i), bB + 20, hLabel(h), { anchor: 'middle', size: 12.5, fill: C.ink }); });
  s += L(x0, bB, x1, bB, C.ink, 1.1);
  s += legend(x0 - 70, 16, [
    { kind: 'rect', color: C.purple, label: 'WDO · mini dólar' },
    { kind: 'rect', color: C.orange, label: 'WIN · mini índice' },
    { kind: 'band', color: C.band, label: 'faixa de acaso (margem de erro de 95%)' },
  ], 24);
  return svg(W, H, s);
}

// ================= Slide 5: depois do pico =================
function chartDepois() {
  const W = 800, H = 470;
  let s = '';
  const panels = [
    { rows: D.dep_wdo, name: 'WDO · mini dólar', col: C.purple, y0: 30 },
    { rows: D.dep_win, name: 'WIN · mini índice', col: C.orange, y0: 235 },
  ];
  const x0 = 60, x1 = 790, step = (x1 - x0) / HORAS.length, cx = i => x0 + step * (i + 0.5);
  for (const p of panels) {
    const top = p.y0 + 22, bot = p.y0 + 172, sy = lin(36, 58, bot, top);
    s += T(0, p.y0 + 8, p.name, { size: 14, weight: 700 });
    for (const v of [40, 45, 50, 55]) s += L(x0, sy(v), x1, sy(v), C.grid) + T(x0 - 8, sy(v) + 4, v + '%', { anchor: 'end', size: 11.5, fill: C.ink2 });
    s += L(x0, bot, x1, bot, C.ink, 1.1);
    HORAS.forEach((h, i) => {
      const r = p.rows.find(q => q.horario === h && q.minutos_depois === 15);
      const x = cx(i);
      s += L(x - 9, sy(r.normal_continua_pct), x + 9, sy(r.normal_continua_pct), C.muted, 4);
      s += L(x, sy(r.continua_pct - r.margem_pct), x, sy(r.continua_pct + r.margem_pct), C.ink, 1.2);
      s += Ci(x, sy(r.continua_pct), 5, p.col);
      if (p.y0 > 100) s += T(x, bot + 18, hLabel(h), { anchor: 'middle', size: 12 });
    });
  }
  s += legend(x0, H - 6, [
    { kind: 'err', color: C.purple, label: 'pico WDO (± margem 95%)' },
    { kind: 'err', color: C.orange, label: 'pico WIN (± margem 95%)' },
    { kind: 'tick', color: C.muted, label: 'minuto comum da mesma hora' },
  ], 16);
  return svg(W, H, s);
}

// ================= Slide 6: alta x baixa (pico do DIA) =================
function chartAltaBaixa() {
  const W = 1180, H = 400;
  const cfg = [
    { k: 'wdo', name: 'WDO · mini dólar', unit: 'pontos (1 pt = R$ 10/contrato)', dec: 2, lim: [-6.5, 4.5], ticks: [-6, -4, -2, 0, 2, 4] },
    { k: 'win', name: 'WIN · mini índice', unit: 'pontos (1 pt = R$ 0,20/contrato)', dec: 1, lim: [-140, 140], ticks: [-100, -50, 0, 50, 100] },
    { k: 'dolarizado', name: 'Índice dolarizado (1000 × WIN ÷ WDO)', unit: 'pontos do Ibovespa em US$', dec: 1, lim: [-36, 36], ticks: [-30, -20, -10, 0, 10, 20, 30] },
  ];
  const offs = [-1, 0, 3, 5, 10, 15], xl = ['T−1', 'T (pico)', 'T+3', 'T+5', 'T+10', 'T+15'];
  const pw = 350, gap = 45;
  let s = '';
  cfg.forEach((c, j) => {
    const ox = 20 + j * (pw + gap), x0 = ox + 55, x1 = ox + pw, top = 50, bot = 330;
    const sx = i => lin(0, 5, x0 + 12, x1 - 12)(i), sy = lin(c.lim[0], c.lim[1], bot, top);
    s += T(ox, 18, c.name, { size: 14.5, weight: 700 });
    s += T(ox + 12, (top + bot) / 2, c.unit, { size: 11.5, fill: C.ink2, anchor: 'middle', rot: -90 });
    for (const v of c.ticks) s += L(x0, sy(v), x1, sy(v), v === 0 ? C.ink : C.grid, v === 0 ? 1.2 : 1) + T(x0 - 7, sy(v) + 4, br(v, 0), { anchor: 'end', size: 11.5, fill: C.ink2 });
    offs.forEach((o, i) => { s += T(sx(i), bot + 20, xl[i], { anchor: 'middle', size: 12 }); });
    const get = t => offs.map(o => D[`p30_${c.k}_${t}`].find(r => r.grupo === 'DIA' && r.offset === o).mediana_pts);
    const series = [['todos', C.muted, '6 4', 2], ['alta', C.purple, '', 3], ['baixa', C.orange, '', 3]];
    for (const [t, col, dash, w] of series) {
      const v = get(t), pts = v.map((y, i) => [sx(i), sy(y)]);
      s += P(pts, col, w, dash);
      pts.forEach((p, i) => {
        s += Ci(p[0], p[1], t === 'todos' ? 3.5 : 5.5, col);
        if (t !== 'todos' && i > 0) s += T(p[0], p[1] + (t === 'alta' ? -11 : 21), br(v[i], c.dec, true), { anchor: 'middle', size: 11.5, weight: 700, fill: t === 'alta' ? C.purple : C.orangeTxt });
      });
    }
    const n = t => D[`p30_${c.k}_${t}`].find(r => r.grupo === 'DIA').n;
    s += T(ox + 55, bot + 44, `n: ${n('alta')} dias de alta · ${n('baixa')} de baixa`, { size: 11.5, fill: C.ink2 });
  });
  s += legend(80, H - 4, [
    { kind: 'line', color: C.purple, label: 'dias de alta (fechamento > abertura)' },
    { kind: 'line', color: C.orange, label: 'dias de baixa' },
    { kind: 'dash', color: C.muted, label: 'todos os dias juntos (alta e baixa se anulam)' },
  ], 28);
  return svg(W, H, s);
}

// ================= Slide 7: fluxo estrangeiro x PF =================
function fluxoStats() {
  const f = D.fluxo, e = f.map(r => r.estrangeiro), p = f.map(r => r.pessoa_fisica), n = e.length;
  const me = e.reduce((a, b) => a + b) / n, mp = p.reduce((a, b) => a + b) / n;
  let cov = 0, ve = 0, vp = 0, op = 0;
  for (let i = 0; i < n; i++) { cov += (e[i] - me) * (p[i] - mp); ve += (e[i] - me) ** 2; vp += (p[i] - mp) ** 2; if (e[i] * p[i] < 0) op++; }
  return { n, corr: cov / Math.sqrt(ve * vp), opostos: op / n * 100, ini: f[0].data.split('-').reverse().join('/'), fim: f[n - 1].data.split('-').reverse().join('/') };
}
function chartFluxo() {
  const W = 760, H = 430, x0 = 60, x1 = 680, top = 20, bot = 340;
  const f = D.fluxo; let ce = 0, cp = 0;
  const pts = f.map(r => { ce += r.estrangeiro; cp += r.pessoa_fisica; return { d: new Date(r.data), e: ce / 1000, p: cp / 1000 }; });
  const sx = lin(+pts[0].d, +pts[pts.length - 1].d, x0, x1), sy = lin(-20, 80, bot, top);
  let s = '';
  for (const v of [-20, 0, 20, 40, 60, 80]) s += L(x0, sy(v), x1, sy(v), v === 0 ? C.ink : C.grid, v === 0 ? 1.2 : 1) + T(x0 - 8, sy(v) + 4, br(v, 0), { anchor: 'end', size: 12, fill: C.ink2 });
  s += T(14, (top + bot) / 2, 'saldo acumulado (R$ bilhões)', { size: 12, fill: C.ink2, anchor: 'middle', rot: -90 });
  const meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  for (let m = 0; m < 13; m += 2) {
    const d = new Date(2025, 11 + m, 1); if (+d > +pts[pts.length - 1].d) break;
    s += T(sx(+d), bot + 20, `${meses[d.getMonth()]}/${String(d.getFullYear()).slice(2)}`, { anchor: 'middle', size: 12 });
  }
  s += P(pts.map(q => [sx(+q.d), sy(q.e)]), C.purple, 3);
  s += P(pts.map(q => [sx(+q.d), sy(q.p)]), C.orange, 3);
  const mx = pts.reduce((a, b) => (b.e > a.e ? b : a));
  s += Ci(sx(+mx.d), sy(mx.e), 5, C.purple) + T(sx(+mx.d), sy(mx.e) - 10, `pico: R$ ${br(mx.e, 0)} bi`, { anchor: 'middle', size: 12, weight: 700, fill: C.purple });
  const last = pts[pts.length - 1];
  s += T(x1 + 8, sy(last.e) + 4, `R$ ${br(last.e, 0)} bi`, { anchor: 'start', size: 12, weight: 700, fill: C.purple });
  s += T(x1 + 8, sy(last.p) + 4, `R$ ${br(last.p, 0)} bi`, { anchor: 'start', size: 12, weight: 700, fill: C.orangeTxt });
  s += legend(x0, H - 6, [
    { kind: 'line', color: C.purple, label: 'investidor estrangeiro' },
    { kind: 'line', color: C.orange, label: 'pessoa física' },
  ], 30);
  return svg(W, H, s);
}

document.addEventListener('DOMContentLoaded', () => {
  const put = (id, html) => { const e = document.getElementById(id); if (e) e.innerHTML = html; };
  put('c-cobertura', chartCobertura());
  put('c-gate1', chartGate1());
  put('c-minuto', chartMinutoPico());
  put('c-depois', chartDepois());
  put('c-altabaixa', chartAltaBaixa());
  put('c-fluxo', chartFluxo());
  const st = fluxoStats();
  document.querySelectorAll('[data-fluxo]').forEach(e => {
    const k = e.dataset.fluxo;
    e.textContent = k === 'corr' ? br(st.corr, 2) : k === 'opostos' ? br(st.opostos, 0) + '%' : st[k];
  });
});
