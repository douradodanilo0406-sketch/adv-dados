#!/usr/bin/env python3
"""
Coletor padronizado — Mapa de Abastecimento FLV (Rio de Janeiro)

Gera, para um ano-base, as quatro camadas da pesquisa em CSVs padronizados:
  1. producao_uf.csv        IBGE/PAM  — produção por UF (quem produz)
  2. precos_ceasarj.csv     Conab/Prohort Diário — preço mensal na CEASA-RJ (quando aperta)
  3. origem_ceasarj.csv     Conab/Prohort Mensal — entrada por UF de origem (quem abastece o Rio)
  4. exportacao_uf.csv      MDIC/Comex Stat — exportação mensal por UF (quanto sai do mercado interno)
  + resumo_fruta.csv        cruzamento final por fruta

Uso:
    pip install pandas requests
    python coletor_flv.py --ano 2025 --saida dados
    python coletor_flv.py --ano 2025 --prohort-mensal ProhortMensal_2025.txt   # arquivo obtido via LAI/painel

Regras (do vault): sempre registrar fonte, data de coleta e unidade; nunca misturar anos;
separar dado oficial de estimativa.
"""
import argparse, datetime as dt, io, json, os, sys
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings()  # Comex Stat e Conab às vezes têm cadeia de certificado incompleta
HOJE = dt.date.today().isoformat()

# ---------------------------------------------------------------- catálogo de frutas
# nome padrão -> (produto PAM, tabela PAM, produtos Prohort, NCM exportação)
FRUTAS = {
    "Laranja":   ("Laranja", "1613", ["LARANJA PERA"], ["08051000"]),
    "Limão":     ("Limão", "1613", ["LIMAO TAHITI"], ["08055000"]),
    "Banana":    ("Banana (cacho)", "1613", ["BANANA NANICA", "BANANA PRATA"], ["08039000"]),
    "Caqui":     ("Caqui", "1613", ["CAQUI"], []),
    "Manga":     ("Manga", "1613", ["MANGA"], ["08045020"]),
    "Uva":       ("Uva", "1613", ["UVA ITALIA", "UVA NIAGARA"], ["08061000"]),
    "Melão":     ("Melão", "1612", ["MELAO AMARELO"], ["08071900"]),
    "Abacaxi":   ("Abacaxi*", "1612", ["ABACAXI"], ["08043000"]),
    "Mamão":     ("Mamão", "1613", ["MAMAO FORMOSA", "MAMAO HAWAY"], ["08072000"]),
    "Maçã":      ("Maçã", "1613", ["MACA"], ["08081000"]),
    "Tangerina": ("Tangerina", "1613", ["TANGERINA"], ["08052100"]),
    "Goiaba":    ("Goiaba", "1613", ["GOIABA"], []),
    "Maracujá":  ("Maracujá", "1613", ["MARACUJA AZEDO"], []),
    "Abacate":   ("Abacate", "1613", ["ABACATE"], []),
    "Melancia":  ("Melancia", "1612", ["MELANCIA"], ["08071100"]),
}
CEASA_RJ = "CEASA/RJ - RIO DE JANEIRO"
URL_PROHORT = "https://portaldeinformacoes.conab.gov.br/downloads/arquivos/{}.txt"
SCHEMA = "flv-abastecimento/1.0"

# Calendário de referência de mercado (Cepea/Conab) — validado ou contestado pelos preços do ano-base.
# meses: 1=jan … 12=dez. None = sem referência registrada no vault.
SAFRA_REF = {
    "Laranja":   {"pico": [5, 6, 7, 8, 9, 10], "entressafra": [12, 1, 2, 3]},
    "Limão":     {"pico": [1, 2, 3, 4], "entressafra": [5, 6, 7, 8, 9, 10]},
    "Banana":    {"pico": [1, 2, 3, 4, 5], "entressafra": [6, 7, 8]},
    "Caqui":     {"pico": [1, 2, 3, 4, 5], "entressafra": [6, 7, 8, 9, 10, 11, 12]},
    "Manga":     {"pico": [10, 11, 12, 1, 2], "entressafra": [5, 6, 7, 8]},
    "Uva":       {"pico": [1, 2, 3], "entressafra": [4, 5, 6, 7, 8, 9, 10, 11, 12],
                  "obs": "Calendário do RS; uva de mesa de PE/BA tem oferta o ano todo, com picos no 2º semestre"},
    "Melão":     {"pico": [8, 9, 10, 11, 12, 1], "entressafra": [2, 3, 4, 5, 6]},
    "Abacaxi":   {"pico": [10, 11, 12, 1], "entressafra": [2, 3, 4, 5]},
    "Mamão":     {"pico": [9, 10, 11, 12, 1, 2, 3], "entressafra": [6, 7, 8]},
    "Maçã":      {"pico": [2, 3, 4, 5], "entressafra": [10, 11, 12, 1],
                  "obs": "Colheita; câmara fria garante oferta o ano todo"},
    "Tangerina": {"pico": [5, 6, 7, 8], "entressafra": [9, 10, 11, 12, 1, 2, 3, 4]},
}
UF_SIGLA = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM", "Bahia": "BA", "Ceará": "CE",
    "Distrito Federal": "DF", "Espírito Santo": "ES", "Goiás": "GO", "Maranhão": "MA", "Mato Grosso": "MT",
    "Mato Grosso do Sul": "MS", "Minas Gerais": "MG", "Pará": "PA", "Paraíba": "PB", "Paraná": "PR",
    "Pernambuco": "PE", "Piauí": "PI", "Rio de Janeiro": "RJ", "Rio Grande do Norte": "RN",
    "Rio Grande do Sul": "RS", "Rondônia": "RO", "Roraima": "RR", "Santa Catarina": "SC",
    "São Paulo": "SP", "Sergipe": "SE", "Tocantins": "TO",
}


def slug(txt):
    import unicodedata
    return unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode().lower().replace(" ", "-")


def log(msg):
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


# ---------------------------------------------------------------- 1. IBGE / PAM
def coletar_pam(ano):
    log(f"IBGE/PAM {ano} …")
    linhas = []
    for tab, cls in (("1613", "c82"), ("1612", "c81")):
        url = f"https://apisidra.ibge.gov.br/values/t/{tab}/n3/all/v/214/p/{ano}/{cls}/all"
        d = requests.get(url, timeout=180).json()[1:]
        for x in d:
            if x["V"] in ("-", "...", "X", ".."):
                continue
            linhas.append({"tabela": tab, "produto_pam": x["D4N"], "uf": x["D1N"],
                           "toneladas": float(x["V"]), "ano": int(x["D3N"])})
    df = pd.DataFrame(linhas)
    nomes = {v[0]: k for k, v in FRUTAS.items()}
    df = df[df.produto_pam.isin(nomes)].copy()
    df["fruta"] = df.produto_pam.map(nomes)
    df["participacao_%"] = df.toneladas / df.groupby("fruta").toneladas.transform("sum") * 100
    df["ranking"] = df.groupby("fruta").toneladas.rank(ascending=False, method="first").astype(int)
    df["fonte"] = f"IBGE/PAM {ano} (SIDRA {tab})"
    df["coleta"] = HOJE
    return df.sort_values(["fruta", "ranking"])


# ---------------------------------------------------------------- 2. Prohort Diário (preços)
def baixar(nome, destino):
    caminho = os.path.join(destino, f"{nome}.txt")
    if not os.path.exists(caminho):
        log(f"baixando {nome}.txt (arquivo grande, pode levar alguns minutos) …")
        cab = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
               "Accept": "*/*", "Accept-Language": "pt-BR,pt;q=0.9",
               "Referer": "https://portaldeinformacoes.conab.gov.br/download-arquivos.html"}
        ultimo = None
        for tentativa in range(3):
            try:
                with requests.get(URL_PROHORT.format(nome), stream=True, timeout=900,
                                  verify=False, headers=cab) as r:
                    r.raise_for_status()
                    with open(caminho + ".tmp", "wb") as f:
                        for bloco in r.iter_content(1 << 20):
                            f.write(bloco)
                os.replace(caminho + ".tmp", caminho)
                break
            except Exception as e:
                ultimo = e
                log(f"tentativa {tentativa + 1} falhou: {e}")
                import time; time.sleep(10 * (tentativa + 1))
        else:
            raise ultimo
    return caminho


def ler_prohort(caminho, **kw):
    df = pd.read_csv(caminho, sep=";", encoding="latin1", dtype=str, **kw)
    for c in df.columns:
        df[c] = df[c].str.strip()
    return df


def coletar_precos(ano, destino):
    df = ler_prohort(baixar("ProhortDiario", destino),
                     usecols=["dsc_ceasa", "dsc_produto", "sig_unidade_medida", "data_preco", "preco_diario"])
    df = df[df.dsc_ceasa == CEASA_RJ].copy()
    df["data"] = pd.to_datetime(df.data_preco.str[:10], format="%Y/%m/%d", errors="coerce")
    df = df[df.data.dt.year == ano]
    df["preco"] = pd.to_numeric(df.preco_diario, errors="coerce")
    mapa = {p: k for k, v in FRUTAS.items() for p in v[2]}
    df = df[df.dsc_produto.isin(mapa)]
    out = (df.groupby(["dsc_produto", "sig_unidade_medida", df.data.dt.month])
             .agg(preco_medio=("preco", "mean"), dias=("preco", "size"),
                  valores_distintos=("preco", "nunique")).reset_index()
             .rename(columns={"data": "mes", "dsc_produto": "produto_prohort", "sig_unidade_medida": "unidade"}))
    out["fruta"] = out.produto_prohort.map(mapa)
    out["indice_sazonal"] = out.preco_medio / out.groupby("produto_prohort").preco_medio.transform("mean") * 100
    out["fonte"] = "Conab/Prohort Diário — CEASA/RJ Rio de Janeiro"
    out["coleta"] = HOJE
    # alerta de qualidade: preço repetido o mês inteiro pode indicar valor replicado, não cotação real
    out["alerta_qualidade"] = (out.valores_distintos <= 1) & (out.dias > 5)
    return out


# ---------------------------------------------------------------- 3. Prohort Mensal (origem)
def coletar_origem(ano, destino, arquivo=None):
    caminho = arquivo or baixar("ProhortMensal", destino)
    df = ler_prohort(caminho)
    df = df[(df.dsc_ceasa == CEASA_RJ) & (df.id_ano_comercializacao == str(ano))].copy()
    if df.empty:
        log(f"ATENÇÃO: o arquivo Prohort Mensal não tem dados de {ano} para a CEASA-RJ. "
            "Obter via painel Prohort ou pedido LAI (ver Protocolo).")
        return pd.DataFrame()
    df["kg"] = pd.to_numeric(df.qtd_comercializada_kg, errors="coerce")
    df["valor"] = pd.to_numeric(df.valor_comercializado.str.replace(",", "."), errors="coerce")
    mapa = {p: k for k, v in FRUTAS.items() for p in v[2]}
    df["fruta"] = df.dsc_produto.map(mapa)
    df = df[df.fruta.notna()]
    out = (df.groupby(["fruta", "id_mes_comercializacao", "uf_origem_produto"])
             .agg(kg=("kg", "sum"), valor=("valor", "sum")).reset_index()
             .rename(columns={"id_mes_comercializacao": "mes", "uf_origem_produto": "uf_origem"}))
    out["mes"] = out.mes.astype(int)
    out["participacao_%"] = out.kg / out.groupby(["fruta", "mes"]).kg.transform("sum") * 100
    out["preco_medio_kg"] = out.valor / out.kg
    out["fonte"] = "Conab/Prohort Mensal — CEASA/RJ Rio de Janeiro"
    out["coleta"] = HOJE
    return out.sort_values(["fruta", "mes", "kg"], ascending=[True, True, False])


# ---------------------------------------------------------------- 4. Comex Stat (exportação)
def coletar_exportacao(ano):
    log(f"Comex Stat {ano} …")
    ncms = sorted({n for v in FRUTAS.values() for n in v[3]})
    body = {"flow": "export", "monthDetail": True,
            "period": {"from": f"{ano}-01", "to": f"{ano}-12"},
            "filters": [{"filter": "ncm", "values": ncms}],
            "details": ["ncm", "state"], "metrics": ["metricKG", "metricFOB"]}
    r = requests.post("https://api-comexstat.mdic.gov.br/general", json=body, timeout=180, verify=False)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["data"]["list"])
    ncm_fruta = {n: k for k, v in FRUTAS.items() for n in v[3]}
    df["fruta"] = df.coNcm.astype(str).str.zfill(8).map(ncm_fruta)
    df["toneladas"] = pd.to_numeric(df.metricKG) / 1000
    df["us_fob"] = pd.to_numeric(df.metricFOB)
    df = df.rename(columns={"monthNumber": "mes", "state": "uf"})[["fruta", "mes", "uf", "toneladas", "us_fob"]]
    df["mes"] = pd.to_numeric(df.mes).astype(int)  # a API devolve o mês como texto ("09")
    df["fonte"] = f"MDIC/Comex Stat {ano}"
    df["coleta"] = HOJE
    return df


# ---------------------------------------------------------------- cruzamento
def resumo(pam, precos, origem, exp):
    linhas = []
    for fruta in FRUTAS:
        p = pam[pam.fruta == fruta].sort_values("ranking")
        lin = {"fruta": fruta}
        for i, (_, r) in enumerate(p.head(3).iterrows(), 1):
            lin[f"produtor_{i}"] = f"{r.uf} ({r['participacao_%']:.0f}%)"
        rj = p[p.uf == "Rio de Janeiro"]
        lin["rj_ranking"] = int(rj.ranking.iloc[0]) if len(rj) else None
        pr = precos[precos.fruta == fruta].groupby("mes").preco_medio.mean()
        if len(pr):
            lin["mes_preco_min"], lin["mes_preco_max"] = int(pr.idxmin()), int(pr.idxmax())
            lin["amplitude_preco_%"] = round((pr.max() / pr.min() - 1) * 100)
        e = exp[exp.fruta == fruta].groupby("mes").toneladas.sum() if len(exp) else pd.Series(dtype=float)
        e.index = e.index.astype(int)
        if len(e):
            lin["exportacao_t"] = round(e.sum())
            lin["mes_pico_exportacao"] = int(e.idxmax())
        if len(origem):
            o = origem[origem.fruta == fruta].groupby("uf_origem").kg.sum().sort_values(ascending=False)
            if len(o):
                lin["origem_principal_rj"] = "; ".join(f"{k} {v / o.sum() * 100:.0f}%" for k, v in o.head(3).items())
        linhas.append(lin)
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------- arquivo único para o app
def exportar_app(ano, pam, precos, origem, exp, caminho):
    """Gera um JSON pequeno e autoexplicativo para o PedidoFlow ler direto (cache local, offline)."""
    frutas = []
    for fruta, (_, _, prods, ncms) in FRUTAS.items():
        p = pam[pam.fruta == fruta].sort_values("ranking")
        rj = p[p.uf == "Rio de Janeiro"]
        pr = precos[precos.fruta == fruta]
        mensal = []
        if len(pr):
            g = pr.groupby("mes").agg(preco=("preco_medio", "mean"), alerta=("alerta_qualidade", "any"))
            media = g.preco.mean()
            for mes, r in g.iterrows():
                mensal.append({"mes": int(mes), "preco": round(float(r.preco), 2),
                               "indice": round(float(r.preco / media * 100)), "alerta_preco_repetido": bool(r.alerta)})
        e = exp[exp.fruta == fruta].groupby("mes").toneladas.sum() if len(exp) else pd.Series(dtype=float)
        e.index = e.index.astype(int)
        o = origem[origem.fruta == fruta] if len(origem) else pd.DataFrame()
        origem_mensal = None
        if len(o):
            origem_mensal = [{"mes": int(m), "ufs": [{"uf": r.uf_origem, "kg": round(float(r.kg)),
                                                      "pct": round(float(r["participacao_%"]), 1)}
                                                     for _, r in g.head(5).iterrows()]}
                             for m, g in o.groupby("mes")]
        sinais = {}
        if mensal:
            pmin = min(mensal, key=lambda x: x["preco"]); pmax = max(mensal, key=lambda x: x["preco"])
            sinais = {"mes_preco_min": pmin["mes"], "mes_preco_max": pmax["mes"],
                      "amplitude_pct": round((pmax["preco"] / pmin["preco"] - 1) * 100)}
            ref = SAFRA_REF.get(fruta)
            if ref:  # o preço máximo cair na entressafra de referência confirma o calendário
                sinais["calendario_confirmado_pelo_preco"] = pmax["mes"] in ref["entressafra"]
        if len(e):
            sinais["mes_pico_exportacao"] = int(e.idxmax())
        frutas.append({
            "id": slug(fruta), "nome": fruta, "produtos_prohort": prods, "ncm_exportacao": ncms,
            "unidade_preco": pr.unidade.iloc[0] if len(pr) else None,
            "producao": {
                "total_t": round(float(p.toneladas.sum())) if len(p) else None,
                "produtores": [{"uf": UF_SIGLA.get(r.uf, r.uf), "t": round(float(r.toneladas)),
                                "pct": round(float(r["participacao_%"]), 1)} for _, r in p.head(3).iterrows()],
                "rj": {"t": round(float(rj.toneladas.iloc[0])), "ranking": int(rj.ranking.iloc[0])} if len(rj) else None,
            },
            "safra_referencia": SAFRA_REF.get(fruta),
            "preco_mensal_ceasarj": mensal,
            "exportacao_mensal_t": [round(float(e.get(m, 0))) for m in range(1, 13)] if len(e) else None,
            "origem_mensal_ceasarj": origem_mensal,
            "sinais": sinais,
            "certeza": {"producao": "oficial", "preco": "oficial", "exportacao": "oficial",
                        "safra_referencia": "referencia_de_mercado",
                        "origem": "oficial" if origem_mensal else "pendente"},
        })
    doc = {
        "schema": SCHEMA, "ano_base": ano, "gerado_em": HOJE, "praca": CEASA_RJ,
        "fontes": {
            "producao": f"IBGE/PAM {ano} — SIDRA 1612/1613",
            "preco": "Conab/Prohort Diário — CEASA/RJ Rio de Janeiro",
            "origem": "Conab/Prohort Mensal — CEASA/RJ Rio de Janeiro",
            "exportacao": f"MDIC/Comex Stat {ano}",
            "safra_referencia": "Cepea/HF Brasil e Conab (referência de mercado)",
        },
        "frutas": frutas,
    }
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=2025)
    ap.add_argument("--saida", default="dados")
    ap.add_argument("--prohort-mensal", default=None, help="arquivo Prohort Mensal com o ano-base (LAI/painel)")
    a = ap.parse_args()
    pasta = os.path.join(a.saida, str(a.ano)); os.makedirs(pasta, exist_ok=True)
    cache = a.saida

    pam = coletar_pam(a.ano); pam.to_csv(f"{pasta}/producao_uf.csv", index=False)
    precos = coletar_precos(a.ano, cache); precos.to_csv(f"{pasta}/precos_ceasarj.csv", index=False)
    origem = coletar_origem(a.ano, cache, a.prohort_mensal)
    if len(origem): origem.to_csv(f"{pasta}/origem_ceasarj.csv", index=False)
    exp = coletar_exportacao(a.ano); exp.to_csv(f"{pasta}/exportacao_uf.csv", index=False)
    res = resumo(pam, precos, origem, exp); res.to_csv(f"{pasta}/resumo_fruta.csv", index=False)
    exportar_app(a.ano, pam, precos, origem, exp, f"{pasta}/mapa_abastecimento_{a.ano}.json")
    json.dump({"ano_base": a.ano, "coleta": HOJE, "origem_disponivel": bool(len(origem)),
               "alertas_preco_repetido": int(precos.alerta_qualidade.sum())},
              open(f"{pasta}/metadados.json", "w"), ensure_ascii=False, indent=2)
    log(f"pronto: {pasta}/")
    print(res.to_string(index=False))


if __name__ == "__main__":
    main()
