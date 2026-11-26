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

## Estrutura

```
robo/gerar_adv_dados.py        orquestrador (coleta → cruza → valida → publica)
robo/coletor_flv.py            base anual (IBGE/PAM, Prohort, Comex Stat)
robo/coletor_precos_ceasas.py  comparativo entre praças (Prohort + CEAGESP)
base/                          base anual (sazonalidade)
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
