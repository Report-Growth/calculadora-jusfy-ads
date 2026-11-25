"""Descobre os IDs de segmentação: estados do Brasil e cidades principais."""
import json, sys, unicodedata
from _ads import client, default_cid

def norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()

# (cidade, UF, capital?)
CIDADES = [
    ("Rio Branco","AC",1),("Maceio","AL",1),("Macapa","AP",1),("Manaus","AM",1),("Salvador","BA",1),
    ("Fortaleza","CE",1),("Brasilia","DF",1),("Vitoria","ES",1),("Goiania","GO",1),("Sao Luis","MA",1),
    ("Cuiaba","MT",1),("Campo Grande","MS",1),("Belo Horizonte","MG",1),("Belem","PA",1),("Joao Pessoa","PB",1),
    ("Curitiba","PR",1),("Recife","PE",1),("Teresina","PI",1),("Rio de Janeiro","RJ",1),("Natal","RN",1),
    ("Porto Alegre","RS",1),("Porto Velho","RO",1),("Boa Vista","RR",1),("Florianopolis","SC",1),("Sao Paulo","SP",1),
    ("Aracaju","SE",1),("Palmas","TO",1),
    ("Campinas","SP",0),("Guarulhos","SP",0),("Sao Bernardo do Campo","SP",0),("Santo Andre","SP",0),("Osasco","SP",0),
    ("Ribeirao Preto","SP",0),("Sorocaba","SP",0),("Sao Jose dos Campos","SP",0),("Santos","SP",0),("Sao Jose do Rio Preto","SP",0),
    ("Uberlandia","MG",0),("Contagem","MG",0),("Juiz de Fora","MG",0),("Montes Claros","MG",0),
    ("Niteroi","RJ",0),("Sao Goncalo","RJ",0),("Duque de Caxias","RJ",0),("Nova Iguacu","RJ",0),("Campos dos Goytacazes","RJ",0),
    ("Joinville","SC",0),("Blumenau","SC",0),("Londrina","PR",0),("Maringa","PR",0),("Cascavel","PR",0),
    ("Caxias do Sul","RS",0),("Pelotas","RS",0),("Feira de Santana","BA",0),("Vitoria da Conquista","BA",0),
    ("Jaboatao dos Guararapes","PE",0),("Caruaru","PE",0),("Aparecida de Goiania","GO",0),("Anapolis","GO",0),
    ("Vila Velha","ES",0),("Serra","ES",0),("Campina Grande","PB",0),("Ananindeua","PA",0),("Juazeiro do Norte","CE",0),
    ("Imperatriz","MA",0),("Mossoro","RN",0),("Dourados","MS",0),("Rondonopolis","MT",0),("Varzea Grande","MT",0),
]

def main():
    c = client(); ga = c.get_service("GoogleAdsService")
    rows = ga.search(customer_id=default_cid(), query="""
        SELECT geo_target_constant.id, geo_target_constant.name, geo_target_constant.canonical_name,
               geo_target_constant.target_type, geo_target_constant.status
        FROM geo_target_constant
        WHERE geo_target_constant.country_code = 'BR'
          AND geo_target_constant.target_type IN ('State', 'Federal District', 'City')
          AND geo_target_constant.status = 'ENABLED'""")
    geos = [(r.geo_target_constant.id, r.geo_target_constant.name, r.geo_target_constant.canonical_name,
             r.geo_target_constant.target_type) for r in rows]
    estados = [g for g in geos if g[3] in ("State", "Federal District")]
    print(len(geos), "geos;", len(estados), "estados/DF", file=sys.stderr)
    for e in estados: print("EST", e, file=sys.stderr)
    json.dump({"estados": estados, "cidades_all": [g for g in geos if g[3] == "City"]},
              open("geos_raw.json", "w", encoding="utf-8"), ensure_ascii=False)

if __name__ == "__main__":
    main()
