# AdV Dados

Robô de dados do **Assistente de Vendas (AdV)**. Ele coleta preços e informações públicas de hortifrúti, cruza tudo e publica um arquivo único pronto, que o app baixa sozinho. O celular só mostra; nada pesado roda nele.

Aqui ficam **só dados públicos**. Vendas, custos e clientes da empresa nunca entram neste repositório.

## Arquivo para o app

```
https://raw.githubusercontent.com/douradodanilo0406-sketch/adv-dados/main/publico/adv-dados.json
```

`publico/status.json` mostra como foi a última rodada: fontes ok ou com falha, e avisos. `historico/AAAA-MM-DD.json` guarda uma cópia de cada rodada.

## Quando roda

Segunda, quarta e sexta às 07:00 (horário de Brasília), pelo GitHub Actions. São os dias do boletim do CEAGESP. Também dá para rodar à mão em **Actions → Coleta AdV Dados → Run workflow**.

## Fontes

| Fonte | O que traz | Frequência | Certeza |
| :--- | :--- | :--- | :--- |
| Conab/Prohort Diário | Preço por dia na CEASA-RJ, no CEAGESP SP e na CEASA Campinas (R$/kg) | A cada rodada; os dados chegam com cerca de 3 semanas de atraso | oficial |
| CEAGESP, boletim do Entreposto da Capital | Preço por classificação: menor, comum e maior (R$/kg) | A cada rodada; o histórico vai sendo acumulado em `dados/ceagesp_capital.csv` | oficial |
| IBGE/PAM + Comex Stat + Prohort do ano-base | Sazonalidade, produção por estado e exportação | Base anual, regenerada a cada 30 dias | oficial / referência |

## Regras

- Se uma fonte falhar, o robô mantém o último dado bom dela e marca a falha em `fontes`. Ele nunca publica um arquivo pela metade.
- Preço zero ou negativo é descartado. Uma variação de mais de 4 vezes em relação à rodada anterior também é descartada, e o valor anterior é mantido.
- Os textos de tendência, como "Costuma subir 50% até jan", são **estimativas** pelo padrão do ano-base e sempre vêm com esse rótulo.
- As regras de cálculo são as da Etapa 2 do app e estão testadas em `tests/test_regras.py`.

## Itens acompanhados e calibragem

A lista de itens fica em um lugar só: **`config/itens.json`**. Hoje são 15 frutas, calibradas uma a uma. Para cada item, o arquivo diz como ele aparece em cada fonte: o nome na Conab, o nome no CEAGESP, a linha na tabela de safra do CEAGESP, o produto no IBGE e os códigos de exportação. Nenhum item está fixo no código.

**[CALIBRAGEM.md](CALIBRAGEM.md)** é refeito a cada coleta. Ele mostra, item por item, se cada fonte achou o produto e o que o app vai mostrar no mês. Também aponta problemas: preço parado na Conab, diferença grande entre praças e preço que contradiz o calendário de safra.

Regras de calibragem:
- **Comparação entre praças:** só pela variedade de referência, que é a primeira da lista (por exemplo, Banana Prata contra Banana Prata). Nunca é feita pela média de variedades diferentes.
- **Preço parado:** se o preço fica no mesmo valor por 28 dias na Conab, o dado é marcado com `confianca: baixa`.
- **Safra contra preço:** se o preço do Rio contradiz o calendário de safra, o app não mostra "Em safra" ou "Entressafra" e mostra "padrão em investigação".
- **Item sem calendário de referência (Cepea):** a safra sai do volume de entrada do CEAGESP (tabela oficial 2023–2025, `base/sazonalidade_ceagesp.csv`).
- **Importados:** ficam sempre fora.

### Como incluir um item novo

1. Rode `python robo/calibrar.py --sugerir NOME` (exemplo: `--sugerir tomate`). O comando mostra os nomes em cada fonte e imprime um bloco pronto.
2. Cole o bloco em `config/itens.json` com `"ativo": false`. Revise a variedade de referência, o `pam`, o `ncm` e a `safra`.
3. Rode o robô e o `calibrar.py`, e confira o item no `CALIBRAGEM.md`.
4. Troque para `"ativo": true`. Na rodada seguinte, a base anual é refeita sozinha e o item entra no arquivo do app.

Legumes e verduras já funcionam: com `"grupo": "LEGUMES"` ou `"VERDURAS"`, o robô passa a baixar também esse boletim do CEAGESP.

A tabela de safra do CEAGESP sai cerca de 1 vez por ano. Quando sair uma nova, rode `pip install pdfplumber` e depois `python robo/ler_sazonalidade_ceagesp.py --pdf arquivo.pdf --periodo 2024-2026`.

## Estrutura

```
config/itens.json              catálogo único de itens (o que acompanhar e como achar em cada fonte)
robo/catalogo.py               lê o catálogo
robo/calibrar.py               relatório de calibragem e --sugerir para itens novos
robo/ler_sazonalidade_ceagesp.py  lê a tabela oficial de safra (volume) do CEAGESP
robo/gerar_adv_dados.py        orquestrador (coleta → cruza → valida → publica)
robo/coletor_flv.py            base anual (IBGE/PAM, Prohort, Comex Stat)
robo/coletor_precos_ceasas.py  comparativo entre praças (Prohort + CEAGESP)
base/                          base anual (sazonalidade de preço) e tabela de volume CEAGESP
dados/                         séries acumuladas (Prohort comparativo, CEAGESP)
publico/                       o que o app baixa
historico/                     uma cópia por rodada
```

## Rodar no computador (plano B)

```
pip install -r requirements.txt
python robo/gerar_adv_dados.py            # rodada normal
python robo/gerar_adv_dados.py --anual    # regenera a base anual
```
