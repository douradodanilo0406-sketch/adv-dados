# Calibragem do robô — 9 de 15 itens sem pendência

Gerado em 26/11/2026 22:56. Catálogo: `config/itens.json` (15 itens ativos). Este arquivo é refeito a cada coleta.

| Item | Status | O que o app mostra neste mês |
| :--- | :---: | :--- |
| Laranja | ok | barato · Costuma subir 50% até jan · Entressafra começa em dez |
| Limão | ok | normal · Costuma cair 14% até fev |
| Banana | ok | normal · Preço costuma ficar estável nos próximos meses |
| Caqui | ok | Sem cotação diária na CEASA-RJ · Em entressafra |
| Manga | ok | barato · Costuma subir 31% até fev · Em safra |
| Uva | ok | normal · Costuma subir 15% até jan (baixa confiança: preço repetido pela Conab) · Em entressafra |
| Melão | **atenção** | normal · Costuma cair 21% até dez |
| Abacaxi | ok | barato · Costuma subir 68% até jan · Em safra |
| Mamão | **atenção** | normal · Costuma subir 21% até fev |
| Maçã | ok | normal · Preço costuma ficar estável nos próximos meses · Em entressafra |
| Tangerina | ok | normal · Preço costuma ficar estável nos próximos meses (baixa confiança: preço repetido pela Conab) · Em entressafra |
| Goiaba | **atenção** | normal · Preço costuma ficar estável nos próximos meses |
| Maracujá | **atenção** | normal · Costuma subir 33% até dez |
| Abacate | **atenção** | muito caro · Costuma subir 23% até dez |
| Melancia | **atenção** | normal · Costuma subir 34% até fev (baixa confiança: preço repetido pela Conab) |

## Laranja — ok

- [x] Conab: preço da variedade de referência: LARANJA PERA: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: Cepea/Conab: pico ['mai', 'jun', 'jul', 'ago', 'set', 'out'], entressafra ['dez', 'jan', 'fev', 'mar']
- [x] Preço confirma o calendário (mais caro na entressafra): mais caro em jan, mais barato em ago
- [x] CEAGESP: produto encontrado no boletim: 1 produto(s) no histórico; 3 linha(s) no último boletim (2026-11-25): LARANJA PERA
- [x] Diferença entre praças dentro do esperado (< 45%): SP -36%, Campinas -12%
- [x] IBGE/PAM: produção encontrada: 16.562.775 t
- [x] Comex Stat: exportação encontrada: 458 t no ano
- Nota: Conab Campinas: preço quase parado na Conab nos últimos 28 dias
- Nota: No CEAGESP e fora do mapeamento (de propósito ou não): LARANJA BAIA, LARANJA LIMA, LARANJA SELETA, LARANJA VALÊNCIA

## Limão — ok

- [x] Conab: preço da variedade de referência: LIMAO TAHITI: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: Cepea/Conab: pico ['jan', 'fev', 'mar', 'abr'], entressafra ['mai', 'jun', 'jul', 'ago', 'set', 'out']
- [x] Preço confirma o calendário (mais caro na entressafra): mais caro em set, mais barato em abr
- [x] CEAGESP: produto encontrado no boletim: 1 produto(s) no histórico; 3 linha(s) no último boletim (2026-11-25): LIMÃO TAITI
- [x] Diferença entre praças dentro do esperado (< 45%): SP -30%, Campinas -7%
- [x] IBGE/PAM: produção encontrada: 1.855.085 t
- [x] Comex Stat: exportação encontrada: 203.703 t no ano
- Nota: Preço repetido o mês inteiro em mar (baixa confiança nesses meses)
- Nota: No CEAGESP e fora do mapeamento (de propósito ou não): LIMÃO ROSA, LIMÃO SICILIANO

## Banana — ok

- [x] Conab: preço da variedade de referência: BANANA PRATA: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: Cepea/Conab: pico ['jan', 'fev', 'mar', 'abr', 'mai'], entressafra ['jun', 'jul', 'ago']
- [x] Preço confirma o calendário (mais caro na entressafra): mais caro em set, mais barato em jun
- [x] CEAGESP: produto encontrado no boletim: 3 produto(s) no histórico; 6 linha(s) no último boletim (2026-11-25): BANANA NANICA, BANANA PRATA MG, BANANA PRATA SP
- [x] Diferença entre praças dentro do esperado (< 45%): SP +40%, Campinas +42%
- [x] IBGE/PAM: produção encontrada: 7.288.960 t
- [x] Comex Stat: exportação encontrada: 80.107 t no ano
- Nota: Preço repetido o mês inteiro em jun (baixa confiança nesses meses)
- Nota: No CEAGESP e fora do mapeamento (de propósito ou não): BANANA MAÇÃ, BANANA OURO VERDE, BANANA TERRA

## Caqui — ok

- [x] Calendário de safra: Cepea/Conab: pico ['jan', 'fev', 'mar', 'abr', 'mai'], entressafra ['jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
- [x] CEAGESP: produto encontrado no boletim: fora de época agora (entressafra): normal não aparecer. 0 produto(s) no histórico; 0 linha(s) no último boletim (2026-11-25)
- [x] IBGE/PAM: produção encontrada: 164.625 t
- [x] Comex Stat: exportação encontrada: 898 t no ano
- Nota: A Conab não cota este item: sem comparação entre praças, só CEAGESP.

## Manga — ok

- [x] Conab: preço da variedade de referência: MANGA: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: Cepea/Conab: pico ['out', 'nov', 'dez', 'jan', 'fev'], entressafra ['mai', 'jun', 'jul', 'ago']
- [x] Preço confirma o calendário (mais caro na entressafra): mais caro em jun, mais barato em jan
- [x] CEAGESP: produto encontrado no boletim: 10 produto(s) no histórico; 19 linha(s) no último boletim (2026-11-25): MANGA BOURBON, MANGA ESPADA, MANGA HADEM, MANGA LOLITA, MANGA OURO, MANGA PALMER, MANGA ROSA, MANGA SHELLY, MANGA TOMMY ATCKINS, MANGA VAN DICK
- [x] Diferença entre praças dentro do esperado (< 45%): SP +16%, Campinas +5%
- [x] IBGE/PAM: produção encontrada: 1.905.559 t
- [x] Comex Stat: exportação encontrada: 290.842 t no ano
- Nota: Conab Campinas: preço quase parado na Conab nos últimos 28 dias

## Uva — ok

- [x] Conab: preço da variedade de referência: UVA ITALIA: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: Cepea/Conab: pico ['jan', 'fev', 'mar'], entressafra ['abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
- [x] Preço confirma o calendário (mais caro na entressafra): mais caro em jan, mais barato em ago
- [x] CEAGESP: produto encontrado no boletim: 3 produto(s) no histórico; 2 linha(s) no último boletim (2026-11-25): UVA NIÁGARA
- [x] Diferença entre praças dentro do esperado (< 45%): SP -16%, Campinas -9%
- [x] IBGE/PAM: produção encontrada: 2.197.707 t
- [x] Comex Stat: exportação encontrada: 62.166 t no ano
- Nota: Conab RJ: preço quase parado na Conab nos últimos 28 dias
- Nota: Preço repetido o mês inteiro em jun, nov, dez (baixa confiança nesses meses)
- Nota: No CEAGESP e fora do mapeamento (de propósito ou não): UVA ARRA 15, UVA ARRA CHERRY CRUSH, UVA BENITAKA, UVA BRASIL, UVA CLARA SEM SEMENTE, UVA CRIMSON, UVA ISIS, UVA MELODIA, UVA MOSCATO, UVA NACIONAL, UVA PRETA COM SEMENTE, UVA PRETA SEM SEMENTE, UVA RED GLOBE, UVA THOMPSON, UVA VERMELHA SEM SEMENTE, UVA VITÓRIA

## Melão — atenção

- [x] Conab: preço da variedade de referência: MELAO AMARELO: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: Cepea/Conab: pico ['ago', 'set', 'out', 'nov', 'dez', 'jan'], entressafra ['fev', 'mar', 'abr', 'mai', 'jun']
- [ ] Preço confirma o calendário (mais caro na entressafra): mais caro em set, mais barato em jun — fora da entressafra: o app esconde o texto de safra e mostra 'padrão em investigação'
- [x] CEAGESP: produto encontrado no boletim: 1 produto(s) no histórico; 4 linha(s) no último boletim (2026-11-25): MELÃO AMARELO
- [x] Diferença entre praças dentro do esperado (< 45%): SP -14%, Campinas +4%
- [x] IBGE/PAM: produção encontrada: 705.848 t
- [x] Comex Stat: exportação encontrada: 283.359 t no ano
- Nota: No CEAGESP e fora do mapeamento (de propósito ou não): MELÃO GÁLIA, MELÃO ORANGE, MELÃO PELE DE SAPO, MELÃO POLPA BRANCA "MATISSE"

## Abacaxi — ok

- [x] Conab: preço da variedade de referência: ABACAXI: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: Cepea/Conab: pico ['out', 'nov', 'dez', 'jan'], entressafra ['fev', 'mar', 'abr', 'mai']
- [x] Preço confirma o calendário (mais caro na entressafra): mais caro em jan, mais barato em dez
- [x] CEAGESP: produto encontrado no boletim: 1 produto(s) no histórico; 3 linha(s) no último boletim (2026-11-25): ABACAXI PÉROLA
- [x] Diferença entre praças dentro do esperado (< 45%): SP -10%, Campinas -20%
- [x] IBGE/PAM: produção encontrada: 1.596.703 t
- [x] Comex Stat: exportação encontrada: 3.422 t no ano
- Nota: Conab Campinas: preço quase parado na Conab nos últimos 28 dias

## Mamão — atenção

- [x] Conab: preço da variedade de referência: MAMAO FORMOSA: RJ 75 dias, SP 45 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: Cepea/Conab: pico ['set', 'out', 'nov', 'dez', 'jan', 'fev', 'mar'], entressafra ['jun', 'jul', 'ago']
- [ ] Preço confirma o calendário (mais caro na entressafra): mais caro em mar, mais barato em jan — fora da entressafra: o app esconde o texto de safra e mostra 'padrão em investigação'
- [x] CEAGESP: produto encontrado no boletim: 2 produto(s) no histórico; 6 linha(s) no último boletim (2026-11-25): MAMÃO FORMOSA, MAMÃO HAVAÍ
- [x] Diferença entre praças dentro do esperado (< 45%): SP -21%, Campinas -18%
- [x] IBGE/PAM: produção encontrada: 1.158.987 t
- [x] Comex Stat: exportação encontrada: 55.163 t no ano

## Maçã — ok

- [x] Conab: preço da variedade de referência: MACA: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: Cepea/Conab: pico ['fev', 'mar', 'abr', 'mai'], entressafra ['out', 'nov', 'dez', 'jan']
- [x] Preço confirma o calendário (mais caro na entressafra): mais caro em jan, mais barato em jul
- [x] CEAGESP: produto encontrado no boletim: 2 produto(s) no histórico; 6 linha(s) no último boletim (2026-11-25): MAÇÃ FUJI, MAÇÃ GALA
- [x] Diferença entre praças dentro do esperado (< 45%): SP -3%, Campinas +11%
- [x] IBGE/PAM: produção encontrada: 1.146.297 t
- [x] Comex Stat: exportação encontrada: 13.793 t no ano
- Nota: Conab Campinas: preço quase parado na Conab nos últimos 28 dias

## Tangerina — ok

- [x] Conab: preço da variedade de referência: TANGERINA: RJ 75 dias, SP 46 dias, Campinas 50 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: Cepea/Conab: pico ['mai', 'jun', 'jul', 'ago'], entressafra ['set', 'out', 'nov', 'dez', 'jan', 'fev', 'mar', 'abr']
- [x] Preço confirma o calendário (mais caro na entressafra): mais caro em abr, mais barato em jun
- [x] CEAGESP: produto encontrado no boletim: 3 produto(s) no histórico; 6 linha(s) no último boletim (2026-11-25): MEXERICA RIO, TANGERINA MURCOTE
- [x] Diferença entre praças dentro do esperado (< 45%): SP -28%, Campinas -33%
- [x] IBGE/PAM: produção encontrada: 1.031.851 t
- [x] Comex Stat: exportação encontrada: 143 t no ano
- Nota: Conab RJ: preço quase parado na Conab nos últimos 28 dias
- Nota: Conab Campinas: preço quase parado na Conab nos últimos 28 dias
- Nota: Preço repetido o mês inteiro em jan, fev, jun, nov, dez (baixa confiança nesses meses)
- Nota: No CEAGESP e fora do mapeamento (de propósito ou não): TANGERINA DECOPOM, TANGERINA OLE

## Goiaba — atenção

- [x] Conab: preço da variedade de referência: GOIABA: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: CEAGESP — volume de entrada 2023–2025: pico ['jan', 'fev', 'mar', 'abr'], entressafra ['jun', 'jul']
- [x] Preço confirma o calendário (mais caro na entressafra): mais caro em jun, mais barato em set
- [x] CEAGESP: produto encontrado no boletim: 2 produto(s) no histórico; 6 linha(s) no último boletim (2026-11-25): GOIABA BRANCA, GOIABA VERMELHA
- [ ] Diferença entre praças dentro do esperado (< 45%): SP -48%, Campinas -35%
- [x] IBGE/PAM: produção encontrada: 604.455 t
- [x] Comex Stat: exportação encontrada: 1.082 t no ano
- Nota: Conab RJ: preço quase parado na Conab nos últimos 28 dias
- Nota: Preço repetido o mês inteiro em jun (baixa confiança nesses meses)

## Maracujá — atenção

- [x] Conab: preço da variedade de referência: MARACUJA AZEDO: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: CEAGESP — volume de entrada 2023–2025: pico ['set', 'out'], entressafra ['mai', 'dez']
- [ ] Preço confirma o calendário (mais caro na entressafra): mais caro em set, mais barato em jul — fora da entressafra: o app esconde o texto de safra e mostra 'padrão em investigação'
- [x] CEAGESP: produto encontrado no boletim: 1 produto(s) no histórico; 3 linha(s) no último boletim (2026-11-25): MARACUJÁ AZEDO
- [x] Diferença entre praças dentro do esperado (< 45%): SP -14%, Campinas -1%
- [x] IBGE/PAM: produção encontrada: 864.518 t
- Nota: Conab RJ: preço quase parado na Conab nos últimos 28 dias
- Nota: Conab Campinas: preço quase parado na Conab nos últimos 28 dias
- Nota: No CEAGESP e fora do mapeamento (de propósito ou não): MARACUJÁ DOCE

## Abacate — atenção

- [x] Conab: preço da variedade de referência: ABACATE: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: CEAGESP — volume de entrada 2023–2025: pico ['ago', 'set', 'out', 'nov'], entressafra ['fev', 'mar', 'abr', 'mai']
- [ ] Preço confirma o calendário (mais caro na entressafra): mais caro em dez, mais barato em jun — fora da entressafra: o app esconde o texto de safra e mostra 'padrão em investigação'
- [x] CEAGESP: produto encontrado no boletim: 3 produto(s) no histórico; 4 linha(s) no último boletim (2026-11-25): ABACATE BREDA, ABACATE MARGARIDA
- [x] Diferença entre praças dentro do esperado (< 45%): SP -11%, Campinas +0%
- [x] IBGE/PAM: produção encontrada: 503.627 t
- Nota: No CEAGESP e fora do mapeamento (de propósito ou não): ABACATE AVOCADO/HASS/FUERTE

## Melancia — atenção

- [x] Conab: preço da variedade de referência: MELANCIA: RJ 75 dias, SP 46 dias, Campinas 51 dias
- [x] Base anual: 12 meses de preço na CEASA-RJ: 12 meses no ano-base 2025
- [x] Calendário de safra: CEAGESP — volume de entrada 2023–2025: pico ['out', 'nov', 'dez'], entressafra ['mai', 'jun', 'jul']
- [ ] Preço confirma o calendário (mais caro na entressafra): mais caro em fev, mais barato em jan — fora da entressafra: o app esconde o texto de safra e mostra 'padrão em investigação'
- [x] CEAGESP: produto encontrado no boletim: 1 produto(s) no histórico; 3 linha(s) no último boletim (2026-11-25): MELANCIA
- [x] Diferença entre praças dentro do esperado (< 45%): SP -35%, Campinas -13%
- [x] IBGE/PAM: produção encontrada: 2.251.431 t
- [x] Comex Stat: exportação encontrada: 185.554 t no ano
- Nota: Conab RJ: preço quase parado na Conab nos últimos 28 dias
- Nota: Preço repetido o mês inteiro em nov, dez (baixa confiança nesses meses)
- Nota: No CEAGESP e fora do mapeamento (de propósito ou não): MELANCIA BABY
