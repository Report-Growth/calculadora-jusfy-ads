# Calculadora Jusfy Ads

Estima, por área do direito e região (cidade, estado ou Brasil), quantas pessoas buscam um advogado no Google e quantas conversas no WhatsApp um investimento mensal deve gerar.

Site: publicado pelo GitHub Pages a partir da pasta `docs/`.

## De onde vêm os números

- **Buscas por mês**: Planejador de Palavras-chave do Google Ads (média dos últimos 12 meses, Rede de Pesquisa, português), somando os termos "advogado + área" de `keywords.json`, por local de quem pesquisa. Brasil, 27 estados e as cidades que o Google segmenta.
- **Cidades com pouco dado**: volume estimado pela parcela da cidade nas buscas por "advogado" dentro do estado.
- **Premissas** (CTR, CPC pago em relação ao lance do Planejador, taxa de clique que vira conversa e alcance por busca): calibradas com as campanhas reais da Jusfy Agency. O site publica só os números agregados, sem nome de cliente.

## Como atualizar os dados

Precisa do conector Google Ads configurado na máquina: aponte `GOOGLE_ADS_CONECTOR_DIR` para a pasta com o `.env` das credenciais (nunca neste repositório).

```
python geos.py          # IDs de estados e cidades
python fetch.py         # Planejador por local (retomável; ~1h para todas as cidades)
python bench.py         # campanhas da Agency (somente leitura)
python build_data.py    # gera docs/dados.json
```

Para mudar os termos de uma área, edite `keywords.json` e apague `raw.jsonl` antes de rodar o `fetch.py`.
