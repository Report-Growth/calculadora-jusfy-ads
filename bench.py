"""Benchmarks reais das contas da Jusfy Agency (somente leitura): CTR, CPC e taxa de contato por campanha."""
import json
from _ads import client

LOGIN = "1525377447"; MCC = "9730166300"

def main():
    c = client(LOGIN); ga = c.get_service("GoogleAdsService")
    contas = [(r.customer_client.id, r.customer_client.descriptive_name) for r in ga.search(customer_id=MCC, query="""
        SELECT customer_client.id, customer_client.descriptive_name FROM customer_client
        WHERE customer_client.manager = FALSE AND customer_client.status = 'ENABLED'""")]
    out = []
    for cid, nome in contas:
        try:
            rows = ga.search(customer_id=str(cid), query="""
                SELECT campaign.name, campaign.status, metrics.impressions, metrics.clicks, metrics.cost_micros,
                       metrics.conversions, metrics.search_impression_share, metrics.search_budget_lost_impression_share,
                       metrics.search_rank_lost_impression_share
                FROM campaign
                WHERE segments.date DURING LAST_30_DAYS AND campaign.advertising_channel_type = 'SEARCH'
                  AND metrics.impressions > 0""")
            for r in rows:
                m = r.metrics
                out.append({"conta": nome, "campanha": r.campaign.name, "imp": m.impressions, "cliques": m.clicks,
                            "custo": round(m.cost_micros / 1e6, 2), "conv": round(m.conversions, 1),
                            "is": round(m.search_impression_share, 3), "is_perd_orc": round(m.search_budget_lost_impression_share, 3),
                            "is_perd_rank": round(m.search_rank_lost_impression_share, 3)})
        except Exception as e:
            print("erro", nome, str(e)[:120])
    json.dump(out, open("bench.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(contas), "contas;", len(out), "campanhas")
    for o in out:
        ctr = o["cliques"] / o["imp"] * 100; cpc = o["custo"] / o["cliques"] if o["cliques"] else 0
        tx = o["conv"] / o["cliques"] * 100 if o["cliques"] else 0
        print(f'{o["campanha"][:60]:60} imp {o["imp"]:6} clq {o["cliques"]:5} R${o["custo"]:8.0f} CTR {ctr:4.1f}% CPC {cpc:5.2f} conv {o["conv"]:5} tx {tx:4.1f}% IS {o["is"]}')

if __name__ == "__main__":
    main()
