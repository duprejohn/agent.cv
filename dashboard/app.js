// Search Desk: shared renderer for dashboard.html, roles.html and network.html.
// Data comes from data.js (window.DATA), written by scripts/build_dashboard.py. Each block only runs if its element is on the page.
(() => {
const D = window.DATA || {};
const TODAY = D.today || new Date().toISOString().slice(0, 10);
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const allRoles = D.roles || [], agencies = D.agencies || [], ondeck = D.ondeck || [], outreach = D.outreach || [];
const roles = allRoles.filter(r => r.track !== "contract");
const contracts = allRoles.filter(r => r.track === "contract");
const ORDER = {offer:0,final:1,interviewing:2,"recruiter-screen":3,applied:4,shortlisted:5,sourced:7,passed:8,rejected:9,withdrawn:9,declined:9};
[roles, contracts].forEach(L => L.sort((a, b) => (ORDER[a.stage] ?? 7) - (ORDER[b.stage] ?? 7) || b.fit - a.fit));
const dayName = d => new Date(d + "T12:00:00").toLocaleDateString("en-US", {weekday:"short", month:"short", day:"numeric"});

if ($("stamp")) $("stamp").textContent = "Updated " + TODAY;
if (D.title && $("desk-title")) { $("desk-title").textContent = D.title; document.title = document.title.replace("Search Desk", D.title); }
if ($("desk-sub")) { $("desk-sub").textContent = D.subtitle || ""; $("desk-sub").hidden = !D.subtitle; }

// Pipeline tiles
if ($("funnel")) {
  const stages = [["sourced","Sourced"],["shortlisted","Shortlisted"],["applied","Applied"],["interviewing","Interviewing"],["offer","Offer"]];
  $("funnel").innerHTML = stages.map(([k, l]) => {
    const n = roles.filter(r => r.stage === k || (k === "interviewing" && ["recruiter-screen","interviewing","final"].includes(r.stage))).length;
    return `<div class="${n ? "" : "zero"}"><b>${n}</b><span>${l}</span></div>`;
  }).join("");
}

// On deck
if ($("deck")) {
  const unit = it => it.kind === "Sprint" ? "to send" : it.kind === "Follow-up" ? "due" : "";
  $("deck").innerHTML = ondeck.length ? ondeck.map(it => {
    const st = !it.date ? "" : it.date < TODAY ? "past" : it.date === TODAY ? "today" : "";
    const when = it.date ? `<b>${it.date === TODAY ? "Today" : dayName(it.date)}</b>${esc(it.when || "")}` : `<b>${esc(it.when || "Unscheduled")}</b>`;
    const ref = it.plan || it.ref;
    return `<li class="${st}"><div class="when">${when}</div><div class="what"><div class="title">${esc(it.title)}</div>${it.detail ? `<div class="detail">${esc(it.detail)}</div>` : ""}${ref ? `<div class="ref">${esc(ref)}</div>` : ""}</div><div class="side"><span class="kind k-${esc(it.kind)}">${esc(it.kind)}</span>${it.count ? `<span class="count">${it.count}<small>${unit(it)}</small></span>` : ""}</div></li>`;
  }).join("") : `<li><div class="when"><b>Clear</b></div><div class="what"><div class="title">Nothing on deck</div><div class="detail">Say "prep tomorrow" and Claude will line up the next sprint.</div></div></li>`;
}

// Active conversations (overview): roles past "applied"
if ($("hot")) {
  const hot = allRoles.filter(r => ["recruiter-screen","interviewing","final","offer"].includes(r.stage) || (r.stage === "shortlisted" && /^recruiter/i.test(r.src)));
  $("hot").innerHTML = hot.length ? hot.map(r => `<li><div><div class="co">${r.link ? `<a href="${esc(r.link)}">${esc(r.co)}</a>` : esc(r.co)}</div><div class="role">${esc(r.role)}</div></div><div class="nx"><span class="pill s-${esc(r.stage)}">${esc(r.stage)}</span> ${esc(r.next)}</div></li>`).join("") : `<li><div class="role">No active conversations yet.</div></li>`;
}

// Role tables with filters (roles.html)
const rowHTML = r => `
  <tr class="${r.closed ? "closed" : ""}">
    <td><div class="co">${r.link ? `<a href="${esc(r.link)}">${esc(r.co)}</a>` : esc(r.co)}</div><div class="role">${esc(r.role)}</div><div class="note">${esc(r.note)}</div></td>
    <td><span class="pill s-${esc(r.stage)}">${esc(r.stage)}</span></td>
    <td><span class="fit" role="img" aria-label="Fit ${r.fit} of 5">${[1,2,3,4,5].map(i => `<i class="${i <= r.fit ? "on" : ""}"></i>`).join("")}</span></td>
    <td class="num ${r.payLow ? "pay-low" : ""}">${esc(r.pay)}</td>
    <td>${esc(r.where)}</td>
    <td>${esc(r.next)}</td>
  </tr>`;
if ($("rows")) {
  const F = {
    open: ["Open", r => !r.closed && r.stage !== "sourced"],
    active: ["Talking", r => ["recruiter-screen","interviewing","final","offer"].includes(r.stage)],
    applied: ["Applied", r => r.stage === "applied"],
    queued: ["Queued", r => r.stage === "shortlisted"],
    held: ["On hold", r => r.stage === "sourced"],
    closed: ["Closed", r => r.closed],
    all: ["All", () => true],
  };
  let cur = "open";
  try { cur = localStorage.getItem("roleFilter") || "open"; } catch (e) {}
  if (!F[cur]) cur = "open";
  const draw = () => {
    const list = roles.filter(F[cur][1]);
    $("rows").innerHTML = list.length ? list.map(rowHTML).join("") : `<tr><td colspan="6">Nothing here.</td></tr>`;
    if ($("filters")) $("filters").innerHTML = Object.entries(F).map(([k, [l, fn]]) => `<button type="button" data-f="${k}" aria-pressed="${k === cur}">${l}<span class="cnt">${roles.filter(fn).length}</span></button>`).join("");
  };
  draw();
  if ($("filters")) $("filters").addEventListener("click", e => {
    const b = e.target.closest("button[data-f]"); if (!b) return;
    cur = b.dataset.f; try { localStorage.setItem("roleFilter", cur); } catch (err) {}
    draw();
  });
}
if ($("crows")) $("crows").innerHTML = contracts.length ? contracts.map(rowHTML).join("") : `<tr><td colspan="6">No contract leads yet.</td></tr>`;

// Outreach table
const fmt = d => new Date(d + "T12:00:00").toLocaleDateString("en-US", {month:"short", day:"numeric"});
if ($("orows")) $("orows").innerHTML = outreach.length ? outreach.map(o => `<tr class="${["closed","no-response","declined"].includes(o.stage) ? "closed" : ""}"><td><div class="co">${esc(o.name)}</div><div class="role">${esc(o.org)}${o.rel ? " · " + esc(o.rel) : ""}</div><div class="note">${esc(o.note)}</div></td><td>${esc(o.purpose)}</td><td><span class="pill">${esc(o.stage)}</span></td><td>${o.sent ? fmt(o.sent) : ""}</td><td>${esc(o.next)}</td></tr>`).join("") : `<tr><td colspan="5">No outreach yet. Drafts go in outreach/; sent messages get a row in outreach.csv.</td></tr>`;

// Agencies: summary, progress bars, table
const AGO = {"in-conversation":0, active:0, registered:1, "to-register":2, dormant:3, skip:4};
agencies.sort((a, b) => (AGO[a.stage] ?? 2) - (AGO[b.stage] ?? 2) || a.pri - b.pri);
const agCount = k => agencies.filter(a => a.stage === k).length;
if ($("agsum")) $("agsum").textContent = `${agencies.length} tracked · ${agCount("registered")} registered · ${agCount("in-conversation") + agCount("active")} in conversation · ${agCount("to-register")} to go. Playbook: companies/agencies.md.`;
if ($("agprog")) {
  const live = agencies.filter(a => !["skip","dormant"].includes(a.stage));
  const isConv = a => ["in-conversation","active"].includes(a.stage), isReg = a => a.stage === "registered";
  const row = (label, list) => {
    const n = list.length || 1, c = list.filter(isConv).length, r = list.filter(isReg).length, done = c + r, pct = Math.round(done / n * 100);
    return `<div class="row"><span class="lbl">${label}</span><div class="bar" role="img" aria-label="${label}: ${done} of ${list.length} done, ${c} in conversation, ${r} registered">${c ? `<span class="conv" style="width:${c / n * 100}%" title="In conversation: ${c}"></span>` : ""}${r ? `<span class="reg" style="width:${r / n * 100}%" title="Registered or contacted: ${r}"></span>` : ""}</div><span class="num">${done} of ${list.length} · ${pct}%</span></div>`;
  };
  $("agprog").innerHTML = row("Priority 1", live.filter(a => a.pri === 1)) + row("All agencies", live) +
    `<div class="flowkey" style="margin-top:0"><span><i style="background:var(--good)"></i>In conversation</span><span><i style="background:var(--accent)"></i>Registered or contacted</span><span><i style="background:var(--idle-soft);outline:1px solid var(--line)"></i>To go</span></div>`;
}
if ($("agrows")) $("agrows").innerHTML = agencies.map(a => `<tr class="${["skip","dormant"].includes(a.stage) ? "closed" : ""}"><td><div class="co">${a.url ? `<a href="${esc(a.url)}">${esc(a.name)}</a>` : esc(a.name)}</div><div class="role">${esc(a.model)}</div>${a.contact ? `<div class="note">${esc(a.contact)}</div>` : ""}<div class="note">${esc(a.note)}</div></td><td>${esc(a.cat)}</td><td>${a.pri === 1 ? "<b>1 · now</b>" : a.pri}</td><td><span class="pill">${esc(a.stage)}</span></td><td>${esc(a.how)}</td></tr>`).join("");

// Funnel flow Sankey (plain SVG, no libraries)
if ($("flow") && D.flow && D.flow.found) {
  const F = D.flow, svg = $("flow"), NS = "http://www.w3.org/2000/svg";
  const W = 1000, H = 300, NW = 12, PAD = 14, LABW = 190;
  const cols = [[{k:"found",n:"Roles found",c:"idle"}],
    [{k:"applied",n:"Applied",c:"good"},{k:"queued",n:"Queued to apply",c:"idle"},{k:"held",n:"On hold",c:"idle"},{k:"passed",n:"Passed or closed",c:"idle"}],
    [{k:"screened",n:"Recruiter screens",c:"good"},{k:"waiting",n:"No response yet",c:"idle"},{k:"rejected",n:"Rejected",c:"bad"}],
    [{k:"active",n:"Active",c:"good"},{k:"rejectedAfter",n:"Rejected after screen",c:"bad"}]];
  const links = [["found","applied"],["found","queued"],["found","held"],["found","passed"],["applied","screened"],["applied","waiting"],["applied","rejected"],["screened","active"],["screened","rejectedAfter"]];
  const scale = (H - PAD * 3) / F.found, xs = [0,1,2,3].map(i => i * ((W - LABW - NW) / 3)), N = {};
  const h = v => v > 0 ? Math.max(3, v * scale) : 0;
  cols.forEach((col, i) => {
    let y = i < 2 ? 0 : (N[i === 2 ? "applied" : "screened"] || {y: 0}).y;
    col.forEach(d => { if (!(F[d.k] > 0)) return; N[d.k] = {...d, v: F[d.k], x: xs[i], y, h: h(F[d.k]), out: 0, inn: 0}; y += h(F[d.k]) + PAD; });
  });
  const el = (t, a, p = svg) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); p.appendChild(e); return e; };
  const gl = el("g", {fill: "none"});
  links.forEach(([a, b]) => { const s = N[a], t = N[b]; if (!s || !t) return; const w = h(t.v);
    const y0 = s.y + s.out + w / 2, y1 = t.y + t.inn + w / 2; s.out += w; t.inn += w;
    const x0 = s.x + NW, x1 = t.x, mx = (x0 + x1) / 2;
    const p = el("path", {d: `M${x0},${y0}C${mx},${y0} ${mx},${y1} ${x1},${y1}`, stroke: `var(--${t.c})`, "stroke-opacity": t.c === "idle" ? .22 : .35, "stroke-width": Math.max(2, w)}, gl);
    el("title", {}, p).textContent = `${s.n} → ${t.n}: ${t.v}`; });
  Object.values(N).forEach(d => {
    const r = el("rect", {x: d.x, y: d.y, width: NW, height: d.h, rx: 3, fill: `var(--${d.c})`}); el("title", {}, r).textContent = `${d.n}: ${d.v}`;
    const t = el("text", {x: d.x + NW + 6, y: d.y + d.h / 2, dy: "0.35em", class: "lab"});
    const v = el("tspan", {class: "v"}, t); v.textContent = d.v + " "; const n = el("tspan", {}, t); n.textContent = d.n; });
  if ($("flow-desc")) $("flow-desc").textContent = `${F.found} roles found: ${F.applied} applied, ${F.queued} queued, ${F.held} on hold, ${F.passed} passed or closed. Of those applied: ${F.waiting} awaiting a response, ${F.rejected} rejected, ${F.screened} reached a recruiter screen (${F.active} active, ${F.rejectedAfter} rejected after the screen).`;
}


// Resume page: render the master resume markdown as a document
const inline = t => esc(t).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
const plainResume = md => md.split("\n").map(l => l.startsWith("# ") ? l.slice(2).replace(" | ", "\n")
  : l.startsWith("#### ") ? l.slice(5) : l.startsWith("### ") ? "\n" + l.slice(4) : l.startsWith("## ") ? "\n" + l.slice(3).toUpperCase() : l.replace(/\*\*/g, ""))
  .join("\n").replace(/\n{3,}/g, "\n\n").trim();
const COPY = {};
if ($("resume-doc") && D.resume) {
  const lines = D.resume.md.split("\n");
  let html = "", inList = false, sawName = false, sawContact = false;
  const close = () => { if (inList) { html += "</ul>"; inList = false; } };
  for (const raw of lines) {
    const l = raw.trimEnd();
    if (!l.trim()) { close(); continue; }
    if (l.startsWith("# ")) { close(); const [n, t] = l.slice(2).split(" | "); html += `<p class="rname">${esc(n)}</p>${t ? `<p class="rtag">${esc(t)}</p>` : ""}`; sawName = true; continue; }
    if (sawName && !sawContact && !l.startsWith("#") && !l.startsWith("**")) { html += `<p class="rcontact">${esc(l)}</p>`; sawContact = true; continue; }
    if (/^\*\*.+\*\*$/.test(l) && !html.includes('class="rhead"')) { close(); html += `<p class="rhead">${esc(l.replace(/\*\*/g, ""))}</p>`; continue; }
    if (l.startsWith("#### ")) { close(); const p = l.slice(5).split(" | "); html += `<h5>${esc(p[0])}${p.length > 1 ? `<span>${esc(p[p.length - 1])}</span>` : ""}</h5>`; continue; }
    if (l.startsWith("### ")) { close(); const p = l.slice(4).split(" | "); html += `<h4>${esc(p[0])}${p.length > 1 ? `<span>${esc(p.slice(1).join(" · "))}</span>` : ""}</h4>`; continue; }
    if (l.startsWith("## ")) { close(); html += `<h3>${esc(l.slice(3))}</h3>`; continue; }
    if (l.startsWith("- ")) { if (!inList) { html += "<ul>"; inList = true; } html += `<li>${inline(l.slice(2))}</li>`; continue; }
    close(); html += `<p>${inline(l)}</p>`;
  }
  close();
  $("resume-doc").innerHTML = html;
  COPY["resume-plain"] = plainResume(D.resume.md);
  const bullets = (D.resume.md.match(/^- /gm) || []).length;
  if ($("resume-meta")) $("resume-meta").textContent = `Source: profile/master-resume.md · last edited ${D.resume.updated} · ${bullets} bullets. This is the full master; tailored resumes pick and reorder from it. Ask Claude to change a line here and every future resume follows.`;
}

// Bio page: cards with counts and copy buttons
const card = (b, key) => { COPY[key] = b.text; const words = b.text.trim().split(/\s+/).length;
  return `<div class="card"><div><div class="ct">${esc(b.title)}</div>${b.note ? `<div class="cn">${esc(b.note)}</div>` : ""}</div><div class="tx">${esc(b.text)}</div><div class="ft"><span>${b.text.length} chars · ${words} words · ${esc(b.src)}</span><button type="button" class="copy" data-copy="${key}">Copy</button></div></div>`; };
if ($("bios")) $("bios").innerHTML = (D.bios || []).map((b, i) => card(b, "bio" + i)).join("");
if ($("intake")) $("intake").innerHTML = (D.intake || []).map((b, i) => card(b, "intake" + i)).join("");
document.addEventListener("click", e => {
  const b = e.target.closest && e.target.closest("button.copy[data-copy]"); if (!b) return;
  const text = COPY[b.dataset.copy] || ""; const old = b.textContent;
  const done = ok => { b.textContent = ok ? "Copied" : "Copy failed"; setTimeout(() => { b.textContent = old; }, 1500); };
  try { navigator.clipboard.writeText(text).then(() => done(true), () => done(false)); } catch (err) { done(false); }
});

// Nav counts
if ($("nav-roles")) $("nav-roles").textContent = `Roles (${roles.filter(r => !r.closed && r.stage !== "sourced").length} open)`;
if ($("nav-network")) $("nav-network").textContent = `Network (${agencies.length} agencies)`;
})();
