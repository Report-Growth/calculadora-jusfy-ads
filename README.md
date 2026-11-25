# Calculadora Jusfy Ads

Estima, por área do direito (uma ou várias) e região (estado ou Brasil), quantas pessoas buscam um advogado no Google e quantos cliques de contato no WhatsApp um investimento mensal deve gerar.

Site: publicado pelo GitHub Pages a partir da pasta `docs/`.

## De onde vêm os números

- **Buscas por mês**: Planejador de Palavras-chave do Google Ads (média dos últimos 12 meses, Rede de Pesquisa, português), somando os termos "advogado + área" de `keywords.json`, por local de quem pesquisa: Brasil e 27 estados. As cidades são baixadas só para calibrar o modelo e não vão para o site.
- **CPC**: média real das campanhas da Jusfy Ads, ajustada pela diferença de preço de cada área e estado no Planejador, com piso no 1º quartil real.
- **Premissas** (CTR, parcela das visitas que clica no WhatsApp e alcance por busca): calibradas com as campanhas reais da Jusfy Ads. O site publica só os números agregados, sem nome de cliente.

## Como atualizar os dados

Precisa do conector Google Ads configurado na máquina: aponte `GOOGLE_ADS_CONECTOR_DIR` para a pasta com o `.env` das credenciais (nunca neste repositório).

```
python geos.py          # IDs de estados e cidades
python fetch.py         # Planejador por local (retomável; ~1h para todas as cidades)
python bench.py         # campanhas da Agency (somente leitura)
python build_data.py    # gera docs/dados.json
```

Para mudar os termos de uma área, edite `keywords.json` e apague `raw.jsonl` antes de rodar o `fetch.py`.
