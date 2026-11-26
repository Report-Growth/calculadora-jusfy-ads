"""Gera dados.json (abastece a calculadora) a partir de raw.jsonl + keywords.json + bench.json,
e calibra o modelo com as campanhas reais da Jusfy Agency."""
import json, re, statistics as st, unicodedata
from pathlib import Path
from datetime import date

def norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()

KW = json.load(open("keywords.json", encoding="utf-8"))
AREAS = [a for a in KW if not a.startswith("_")]
GEN = ["advogado", "advogado perto de mim", "escritorio de advocacia"]  # demanda geral por advogado

raw = [json.loads(l) for l in open("raw.jsonl", encoding="utf-8")]
by_id = {r["loc"]["id"]: r for r in raw}
pais = next(r for r in raw if r["loc"]["tipo"] == "pais")
estados = {r["loc"]["uf"]: r for r in raw if r["loc"]["tipo"] == "estado"}

def area_stats(kws, area, drop_noise):
    vol = 0; wl = wh = w = 0
    for k in KW[area]["kws"]:
        v, lo, hi, _ = kws.get(k, [0, 0, 0, ""])
        if drop_noise and v <= 10 and lo == 0:
            continue
        vol += v
        if lo > 0 and hi > 0:
            wl += lo * v; wh += hi * v; w += v
    return vol, (round(wl / w, 2) if w else None), (round(wh / w, 2) if w else None)

def gen_vol(kws):
    return sum(kws.get(k, [0])[0] for k in GEN)

def compute(r):
    t = r["loc"]["tipo"]; kws = r["kws"]
    out_v, out_l, out_h, est = [], [], [], 0
    pai = estados.get(r["loc"]["uf"]) if t == "cidade" else None
    share = (gen_vol(kws) / gen_vol(pai["kws"])) if pai and gen_vol(pai["kws"]) else None
    for i, a in enumerate(AREAS):
        v, lo, hi = area_stats(kws, a, drop_noise=(t == "cidade"))
        if t == "cidade" and share is not None:
            pv, plo, phi = area_stats(pai["kws"], a, False)
            prop = round(pv * share)
            if prop > v:
                v = prop; est |= (1 << i)
            lo = lo or plo; hi = hi or phi
        if lo is None:
            _, lo, hi = area_stats(pais["kws"], a, False)
        out_v.append(v); out_l.append(lo); out_h.append(hi)
    return out_v, out_l, out_h, est

locais = []
for r in raw:
    v, lo, hi, est = compute(r)
    t = r["loc"]["tipo"]
    if t == "cidade" and gen_vol(r["kws"]) < 20:
        continue  # cidade sem dado útil: a calculadora usa o estado
    locais.append({"id": r["loc"]["id"], "t": t[0], "n": r["loc"]["nome"], "uf": r["loc"]["uf"],
                   "v": v, "l": lo, "h": hi, "e": est})
LOC = {l["id"]: l for l in locais}

# Detalhe por palavra-chave (Brasil e estados)
detalhe = {}
for r in [pais] + list(estados.values()):
    detalhe[r["loc"]["id"]] = {k: v[:3] for k, v in r["kws"].items() if v[0] > 0}

# ---------- Calibração com campanhas reais ----------
AREA_TXT = [("trabalh", "trabalhista"), ("famil", "familia"), ("divorc", "familia"), ("consum", "consumidor"),
            ("banc", "bancario"), ("previd", "previdenciario"), ("auxilio", "previdenciario"), ("saude", "medico"),
            ("ambient", "ambiental"), ("civel", "civel")]
bench = [b for b in json.load(open("bench.json", encoding="utf-8")) if b["campanha"].count("|") >= 3]
cal = []
for b in bench:
    partes = [p.strip() for p in b["campanha"].split("|")]
    area = next((a for t, a in AREA_TXT if t in norm(partes[2])), None)
    geo = partes[3]
    loc = None
    m = re.match(r"(.+)-([A-Z]{2})$", geo)
    if m:
        loc = next((l for l in locais if l["t"] == "c" and norm(l["n"]) == norm(m.group(1)) and l["uf"] == m.group(2)), None)
    elif geo in estados:
        loc = LOC.get(estados[geo]["loc"]["id"])
    if not (area and loc) or b["cliques"] < 25 or b["is"] <= 0:
        continue
    i = AREAS.index(area)
    elegiveis = b["imp"] / b["is"]
    # O alcance é medido contra o volume do ESTADO (a calculadora só trabalha com estado/Brasil);
    # contra o volume da cidade o Planejador subestima e o fator infla.
    est = LOC[estados[loc["uf"]]["loc"]["id"]] if loc["t"] == "c" else loc
    cpc = b["custo"] / b["cliques"]
    cal.append({"campanha": b["campanha"], "area": area, "local": loc["n"], "tipo": loc["t"], "busca_planejador": loc["v"][i],
                "busca_estado": est["v"][i],
                "imp_elegiveis": round(elegiveis), "fator_alcance": round(elegiveis / max(est["v"][i], 1), 2),
                "cliques": b["cliques"], "cpc_real": round(cpc, 2), "cpc_plan_low": loc["l"][i], "fator_cpc": round(cpc / loc["l"][i], 2) if loc["l"][i] else None,
                "ctr": round(b["cliques"] / b["imp"], 4), "tx_contato": round(b["conv"] / b["cliques"], 4)})

agg = [b for b in bench]
# Totais pelo histórico completo das campanhas de advogados (bench_hist.json, campanha × mês)
hist = [h for h in json.load(open("bench_hist.json", encoding="utf-8")) if h["campanha"].count("|") >= 2]
I = sum(h["imp"] for h in hist); C = sum(h["cliques"] for h in hist); G = sum(h["custo"] for h in hist); V = sum(h["conv"] for h in hist)
por_camp = {}
for h in hist:
    p = por_camp.setdefault(h["campanha"], [0, 0]); p[0] += h["cliques"]; p[1] += h["custo"]
cpcs = sorted(g / c for c, g in por_camp.values() if c >= 25)
meses = sorted({h["mes"] for h in hist})
calib = {
    "campanhas": len(por_camp), "periodo": [meses[0], meses[-1]], "impressoes": I, "cliques": C, "investimento": round(G), "contatos": V,
    # CPC: média real da Jusfy Ads; o Planejador só diz quanto cada área/estado é mais cara ou mais barata que a referência
    "cpc_piso": round(st.quantiles(cpcs, n=4)[0], 2),
    "cpc_ref_planejador": round(st.median(c["cpc_plan_low"] for c in cal if c["cpc_plan_low"]), 2),
    "ctr": round(C / I, 4), "cpc": round(G / C, 2), "tx_contato": round(V / C, 4), "custo_contato": round(G / V, 2),
    "fator_alcance_mediana": round(st.median(c["fator_alcance"] for c in cal), 2) if cal else None,
    "fator_alcance": round(st.median(fm)) if (fm := [c["fator_alcance"] for c in cal]) else None,
    "n_alcance": len(fm),
    "fator_cpc_mediana": round(st.median(c["fator_cpc"] for c in cal if c["fator_cpc"]), 2) if cal else None,
    "is_mediana": round(st.median(b["is"] for b in agg if b["cliques"] >= 40), 3),
}
# Amostra por campanha tem nome de cliente: fica só local, fora do site público.
json.dump(cal, open("calibracao_local.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

dados = {"meta": {"gerado_em": date.today().isoformat(), "fonte": "Planejador de Palavras-chave do Google Ads (média mensal dos últimos 12 meses, Rede de Pesquisa, português)",
                  "areas": [{"id": a, "nome": KW[a]["nome"], "kws": KW[a]["kws"]} for a in AREAS],
                  "calibracao": calib},
         "locais": [l for l in locais if l["t"] != "c"], "detalhe": detalhe}  # cidades só na calibração
Path("docs").mkdir(exist_ok=True)
json.dump(dados, open("docs/dados.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(locais), "locais;", sum(l["t"] == "c" for l in locais), "cidades")
print(json.dumps(calib, ensure_ascii=False))
for c in cal: print(c)
