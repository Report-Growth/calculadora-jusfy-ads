"""Histórico completo das campanhas da Jusfy Agency por mês (somente leitura, só para análise local)."""
import json
from _ads import client

LOGIN = "1525377447"; MCC = "9730166300"

def main():
    c = client(LOGIN); ga = c.get_service("GoogleAdsService")
    contas = [(r.customer_client.id, r.customer_client.descriptive_name) for r in ga.search(customer_id=MCC, query="""
        SELECT customer_client.id, customer_client.descriptive_name FROM customer_client
        WHERE customer_client.manager = FALSE""")]
    out = []
    for cid, nome in contas:
        try:
            for r in ga.search(customer_id=str(cid), query="""
                SELECT campaign.name, segments.month, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions
                FROM campaign
                WHERE segments.date BETWEEN '2025-01-01' AND '2026-11-24' AND campaign.advertising_channel_type = 'SEARCH'
                  AND metrics.impressions > 0"""):
                m = r.metrics
                out.append({"conta": nome, "campanha": r.campaign.name, "mes": r.segments.month[:7], "imp": m.impressions,
                            "cliques": m.clicks, "custo": round(m.cost_micros / 1e6, 2), "conv": round(m.conversions, 1)})
        except Exception as e:
            print("erro", nome, str(e)[:100])
    json.dump(out, open("bench_hist.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(contas), "contas;", len(out), "linhas campanha×mês")

if __name__ == "__main__":
    main()
