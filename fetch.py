"""Puxa volume e CPC do Planejador para todas as keywords de keywords.json, por local.
Retomável: cada local vira uma linha em raw.jsonl; locais já baixados são pulados.
Ordem: Brasil, estados, cidades (maiores primeiro pela lista de geos.py, depois o resto)."""
import json, sys, time
from pathlib import Path
from google.ads.googleads.errors import GoogleAdsException
from _ads import client, default_cid
from geos import CIDADES, norm

UF = {"Acre":"AC","Alagoas":"AL","Amapa":"AP","Amazonas":"AM","Bahia":"BA","Ceara":"CE","Federal District":"DF",
      "Espirito Santo":"ES","Goias":"GO","Maranhao":"MA","Mato Grosso":"MT","Mato Grosso do Sul":"MS",
      "Minas Gerais":"MG","Para":"PA","Paraiba":"PB","Parana":"PR","Pernambuco":"PE","Piaui":"PI",
      "Rio de Janeiro":"RJ","Rio Grande do Norte":"RN","Rio Grande do Sul":"RS","Rondonia":"RO","Roraima":"RR",
      "Santa Catarina":"SC","Sao Paulo":"SP","Sergipe":"SE","Tocantins":"TO"}

def uf_of(state_name):
    return UF[state_name.replace("State of ", "")]

def locations():
    g = json.load(open("geos_raw.json", encoding="utf-8"))
    locs = [{"id": 2076, "tipo": "pais", "nome": "Brasil", "uf": None}]
    for gid, name, canon, _ in sorted(g["estados"], key=lambda e: uf_of(e[1])):
        locs.append({"id": gid, "tipo": "estado", "nome": name.replace("State of ", ""), "uf": uf_of(name)})
    cidades = []
    for gid, name, canon, _ in g["cidades_all"]:
        parts = canon.split(",")
        if len(parts) != 3:  # Cidade,Estado,Brazil
            continue
        cidades.append({"id": gid, "tipo": "cidade", "nome": name, "uf": uf_of(parts[1])})
    prio = {(norm(n), uf): (0 if cap else 1) for n, uf, cap in CIDADES}
    cidades.sort(key=lambda c: prio.get((norm(c["nome"]), c["uf"]), 2))
    return locs + cidades

def main():
    kw = json.load(open("keywords.json", encoding="utf-8"))
    all_kws = sorted({k for a, v in kw.items() if not a.startswith("_") for k in v["kws"]})
    out = Path("raw.jsonl")
    done = set()
    if out.exists():
        for line in out.open(encoding="utf-8"):
            done.add(json.loads(line)["loc"]["id"])
    locs = [l for l in locations() if l["id"] not in done]
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(locs)
    print(f"{len(all_kws)} keywords; {len(done)} locais prontos; baixando {min(limit, len(locs))}", flush=True)

    c = client(); svc = c.get_service("KeywordPlanIdeaService"); cid = default_cid()
    with out.open("a", encoding="utf-8") as f:
        for i, loc in enumerate(locs[:limit]):
            for tentativa in range(6):
                try:
                    req = c.get_type("GenerateKeywordHistoricalMetricsRequest")
                    req.customer_id = cid
                    req.language = "languageConstants/1014"
                    req.geo_target_constants.append(f"geoTargetConstants/{loc['id']}")
                    req.keyword_plan_network = c.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
                    req.keywords.extend(all_kws)
                    resp = svc.generate_keyword_historical_metrics(request=req)
                    break
                except GoogleAdsException as e:
                    msg = str(e.failure.errors[0].error_code) if e.failure.errors else str(e)
                    espera = 10 * (tentativa + 1)
                    print(f"  erro em {loc['nome']}: {msg.strip()} — nova tentativa em {espera}s", flush=True)
                    time.sleep(espera)
            else:
                print(f"  desisti de {loc['nome']}", flush=True); continue
            res = {}
            for r in resp.results:
                m = r.keyword_metrics
                res[r.text] = [m.avg_monthly_searches or 0,
                               round((m.low_top_of_page_bid_micros or 0) / 1e6, 2),
                               round((m.high_top_of_page_bid_micros or 0) / 1e6, 2),
                               m.competition.name]
                for v in r.close_variants:
                    res.setdefault(v, res[r.text])
            f.write(json.dumps({"loc": loc, "kws": res}, ensure_ascii=False) + "\n"); f.flush()
            if i % 25 == 0:
                print(f"[{i+1}/{min(limit, len(locs))}] {loc['tipo']} {loc['nome']}/{loc['uf']}", flush=True)
            time.sleep(1.1)
    print("fim", flush=True)

if __name__ == "__main__":
    main()
