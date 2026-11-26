#!/usr/bin/env python3
"""
Coletor de preços comparativos entre CEASAs — AdV (Assistente de Vendas)

Compara o preço da mesma mercadoria na CEASA-RJ (referência) com outras praças.
Três fontes, cada uma com seu selo de certeza:

  1. Conab/Prohort Diário (oficial)  — CEASA-RJ, CEAGESP São Paulo e CEASA Campinas.
     Um preço por produto e dia, em R$/kg (abacaxi e coco em R$/unidade). Mesma metodologia
     nas praças, por isso é a base da comparação. Defasagem de ~3 semanas.
  2. CEAGESP direto (oficial)         — boletim do Entreposto da Capital (ceagesp.gov.br/cotacoes).
     Seg/qua/sex, com classificação (tamanho/dúzias) e preço menor/comum/maior em R$/kg.
     O site só mostra os ~6 últimos boletins: rodar pelo menos 1x por semana para formar histórico.
  3. Colubandê (observado)            — a Conab e o boletim da CEASA-RJ não publicam preço da
     unidade de São Gonçalo. Preenchimento manual em dados/precos/colubande_observado.csv.

Saídas (pasta dados/precos/):
  prohort_comparativo.csv     série diária por praça (janela configurável)
  ceagesp_capital.csv         histórico acumulado do boletim CEAGESP (sem duplicar)
  colubande_observado.csv     modelo para preencher à mão (criado se não existir)
  precos_comparativos.json    arquivo único para o app (schema flv-precos-comparativos/1.0)

Uso:
    python scripts/coletor_precos_ceasas.py                      # tudo, janela de 120 dias
    python scripts/coletor_precos_ceasas.py --dias 365 --cache ~/cache_prohort
    python scripts/coletor_precos_ceasas.py --sem-prohort        # só CEAGESP (rápido, para rodar seg/qua/sex)

Regras do cofre: registrar fonte, data e unidade; separar oficial de observado; nunca
comparar fontes diferentes como se fossem a mesma coisa.
"""
import argparse, datetime as dt, io, json, os, re, sys, unicodedata
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coletor_flv import FRUTAS, CEASA_RJ, baixar, ler_prohort, slug, log  # noqa: E402

SCHEMA = "flv-precos-comparativos/1.0"
HOJE = dt.date.today().isoformat()

PRACAS = {
    "ceasa-rj":   {"nome": "CEASA-RJ (Irajá)", "prohort": CEASA_RJ, "uf": "RJ"},
    "ceagesp-sp": {"nome": "CEAGESP São Paulo", "prohort": "CEAGESP - SAO PAULO", "uf": "SP"},
    "campinas":   {"nome": "CEASA Campinas", "prohort": "CEASA/SP - CAMPINAS", "uf": "SP"},
}
REFERENCIA = "ceasa-rj"

# Produto do boletim CEAGESP -> fruta do catálogo. Ordem importa (o primeiro que casar vence).
# Importados ficam de fora para não distorcer a comparação com o Prohort (que é nacional).
CEAGESP_MAPA = [
    ("Laranja", r"^LARANJA PERA$"), ("Limão", r"^LIM[AÃ]O TAITI$"),
    ("Banana", r"^BANANA (NANICA|PRATA)"), ("Caqui", r"^CAQUI"), ("Manga", r"^MANGA"),
    ("Uva", r"^UVA (IT[AÁ]LIA|NIAGARA|NI[AÁ]GARA)"), ("Melão", r"^MEL[AÃ]O AMARELO$"),
    ("Abacaxi", r"^ABACAXI"), ("Mamão", r"^MAM[AÃ]O (FORMOSA|HAVA[IÍ])"), ("Maçã", r"^MA[CÇ][AÃ] "),
    ("Tangerina", r"^TANGERINA (PONKAN|MURCOTE?)"), ("Goiaba", r"^GOIABA"),
    ("Maracujá", r"^MARACUJ[AÁ] AZEDO"), ("Abacate", r"^ABACATE"), ("Melancia", r"^MELANCIA"),
]
URL_CEAGESP = "https://ceagesp.gov.br/cotacoes/"
UA = {"User-Agent": "Mozilla/5.0 (AdV coletor; uso pessoal de pesquisa)"}

COLUBANDE_COLS = ["data", "fruta", "produto", "classificacao", "embalagem", "peso_kg",
                  "preco_embalagem", "preco_kg", "loja_ou_fonte", "observacao"]


# ---------------------------------------------------------------- 1. Prohort comparativo
def coletar_prohort(cache, dias):
    caminho = baixar("ProhortDiario", cache)
    df = ler_prohort(caminho, usecols=["dsc_ceasa", "dsc_produto", "sig_unidade_medida",
                                       "data_preco", "preco_diario"])
    alvo = {v["prohort"]: k for k, v in PRACAS.items()}
    df = df[df.dsc_ceasa.isin(alvo)].copy()
    df["data"] = pd.to_datetime(df.data_preco.str[:10], format="%Y/%m/%d", errors="coerce")
    df["preco"] = pd.to_numeric(df.preco_diario, errors="coerce")
    df = df[df.data >= df.data.max() - pd.Timedelta(days=dias)]
    mapa = {p: f for f, (_, _, prods, _) in FRUTAS.items() for p in prods}
    df["fruta"] = df.dsc_produto.map(mapa)
    df = df[df.fruta.notna() & (df.preco > 0)]
    out = pd.DataFrame({
        "data": df.data.dt.date.astype(str), "praca": df.dsc_ceasa.map(alvo),
        "fruta": df.fruta, "produto_prohort": df.dsc_produto,
        "unidade": df.sig_unidade_medida, "preco": df.preco,
        "fonte": "Conab/Prohort Diário", "certeza": "oficial"})
    log(f"Prohort: {len(out)} preços, {out.data.min()} a {out.data.max()}")
    return out.sort_values(["fruta", "praca", "data"])


# ---------------------------------------------------------------- 2. CEAGESP direto
def _num(x):
    try:
        return float(str(x).replace(".", "").replace(",", "."))
    except ValueError:
        return None


def coletar_ceagesp(grupos=("FRUTAS",)):
    html = requests.get(URL_CEAGESP, headers=UA, timeout=60).text
    m = re.search(r"var Grupos = (\{.*?\});", html)
    if not m:
        log("CEAGESP: não achei a lista de datas — o site pode ter mudado.")
        return pd.DataFrame()
    datas = json.loads(m.group(1))
    linhas = []
    for g in grupos:
        for d in datas.get(g, []):
            r = requests.post(URL_CEAGESP, data={"cot_grupo": g, "cot_data": d}, headers=UA, timeout=60)
            try:
                t = pd.read_html(io.StringIO(r.text), thousands=None)[0]
            except ValueError:
                continue
            t = t.iloc[2:]  # linha 0 = título, linha 1 = cabeçalho
            for _, x in t.iterrows():
                linhas.append({
                    "data": dt.datetime.strptime(d, "%d/%m/%Y").date().isoformat(), "grupo": g,
                    "produto": str(x[0]).strip(), "classificacao": str(x[1]).strip(),
                    "unidade": str(x[2]).strip(), "menor": _num(x[3]), "comum": _num(x[4]),
                    "maior": _num(x[5]), "quilo_embalagem": _num(x[6])})
            log(f"CEAGESP {g} {d}: ok")
    df = pd.DataFrame(linhas)
    if len(df):
        df["fruta"] = df.produto.map(_fruta_ceagesp)
        df["fonte"] = "CEAGESP — Boletim do Entreposto da Capital"
        df["certeza"] = "oficial"
    return df


def _fruta_ceagesp(nome):
    if "IMP" in nome:
        return None
    for fruta, padrao in CEAGESP_MAPA:
        if re.search(padrao, nome):
            return fruta
    return None


def acumular(novo, caminho, chaves):
    if os.path.exists(caminho):
        velho = pd.read_csv(caminho, dtype=str)
        novo = pd.concat([velho, novo.astype(str)]).drop_duplicates(chaves, keep="last")
    novo.to_csv(caminho, index=False)
    return pd.read_csv(caminho)


# ---------------------------------------------------------------- 3. Colubandê (observado)
def ler_colubande(caminho):
    if not os.path.exists(caminho):
        pd.DataFrame(columns=COLUBANDE_COLS).to_csv(caminho, index=False)
        log(f"Criado modelo vazio: {caminho} (preencher à mão)")
        return pd.DataFrame(columns=COLUBANDE_COLS)
    df = pd.read_csv(caminho)
    falta = df.preco_kg.isna() & df.preco_embalagem.notna() & (df.peso_kg > 0)
    df.loc[falta, "preco_kg"] = df.preco_embalagem / df.peso_kg
    return df[df.preco_kg.notna()]


# ---------------------------------------------------------------- 4. JSON para o app
def media_janela(s, ultima, dias=28):
    j = s[pd.to_datetime(s.data) >= pd.to_datetime(ultima) - pd.Timedelta(days=dias)]
    return round(float(j.preco.mean()), 2) if len(j) else None


def exportar(prohort, ceagesp, colubande, caminho):
    frutas = []
    for fruta, (_, _, prods, _) in FRUTAS.items():
        item = {"id": slug(fruta), "nome": fruta, "produtos_prohort": prods,
                "pracas": {}, "comparacao_vs_rj": {}, "ceagesp_classificacoes": [], "colubande": []}
        p = prohort[prohort.fruta == fruta] if len(prohort) else prohort
        for praca in PRACAS:
            s = p[p.praca == praca] if len(p) else p
            if not len(s):
                continue
            ult = s.sort_values("data").iloc[-1]
            item["unidade"] = ult.unidade.strip()
            item["pracas"][praca] = {
                "ultimo": {"data": ult.data, "preco": round(float(ult.preco), 2)},
                "media_28d": media_janela(s, ult.data),
                "fonte": "Conab/Prohort Diário", "certeza": "oficial"}
        ref = item["pracas"].get(REFERENCIA, {}).get("media_28d")
        for praca, v in item["pracas"].items():
            if praca != REFERENCIA and ref and v["media_28d"]:
                item["comparacao_vs_rj"][praca] = round((v["media_28d"] / ref - 1) * 100)
        if len(ceagesp):
            c = ceagesp[ceagesp.fruta == fruta]
            if len(c):
                c = c[c.data == c.data.max()]
                item["ceagesp_classificacoes"] = [
                    {"data": x.data, "produto": x.produto, "classificacao": x.classificacao,
                     "unidade": x.unidade, "menor": x.menor, "comum": x.comum, "maior": x.maior}
                    for x in c.itertuples()]
        if len(colubande):
            c = colubande[colubande.fruta == fruta].sort_values("data").tail(5)
            item["colubande"] = [
                {"data": x.data, "produto": x.produto, "embalagem": x.embalagem,
                 "preco_kg": round(float(x.preco_kg), 2), "fonte": x.loja_ou_fonte,
                 "certeza": "observado"} for x in c.itertuples()]
        frutas.append(item)
    doc = {
        "schema": SCHEMA, "gerado_em": HOJE, "referencia": REFERENCIA,
        "pracas": {k: {"nome": v["nome"], "uf": v["uf"]} for k, v in PRACAS.items()} | {
            "colubande": {"nome": "CEASA-RJ São Gonçalo (Colubandê)", "uf": "RJ"}},
        "fontes": {
            "prohort": {"nome": "Conab/Prohort Diário", "certeza": "oficial",
                        "defasagem": "cerca de 3 semanas", "unidade": "R$/kg (abacaxi: R$/unidade)"},
            "ceagesp": {"nome": "CEAGESP — Boletim do Entreposto da Capital", "certeza": "oficial",
                        "frequencia": "seg, qua e sex", "unidade": "R$/kg por classificação"},
            "colubande": {"nome": "Observação própria", "certeza": "observado",
                          "obs": "Sem fonte pública; preenchido à mão"}},
        "regra_comparacao": "Diferença % = média de 28 dias da praça ÷ média de 28 dias da CEASA-RJ − 1, "
                            "sempre dentro da mesma fonte (Prohort). CEAGESP direto e Colubandê são "
                            "mostrados ao lado, sem entrar no cálculo.",
        "frutas": frutas}
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    log(f"JSON: {caminho}")
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="dados/precos")
    ap.add_argument("--cache", default=os.path.expanduser("~/cache_prohort"))
    ap.add_argument("--dias", type=int, default=120)
    ap.add_argument("--sem-prohort", action="store_true")
    ap.add_argument("--grupos", default="FRUTAS", help="ex.: FRUTAS,LEGUMES,VERDURAS")
    a = ap.parse_args()
    os.makedirs(a.saida, exist_ok=True); os.makedirs(a.cache, exist_ok=True)

    arq_p = f"{a.saida}/prohort_comparativo.csv"
    if a.sem_prohort:
        prohort = pd.read_csv(arq_p) if os.path.exists(arq_p) else pd.DataFrame()
    else:
        prohort = coletar_prohort(a.cache, a.dias); prohort.to_csv(arq_p, index=False)

    novo = coletar_ceagesp(tuple(a.grupos.split(",")))
    arq_c = f"{a.saida}/ceagesp_capital.csv"
    ceagesp = acumular(novo, arq_c, ["data", "grupo", "produto", "classificacao"]) if len(novo) else (
        pd.read_csv(arq_c) if os.path.exists(arq_c) else pd.DataFrame())

    colubande = ler_colubande(f"{a.saida}/colubande_observado.csv")
    doc = exportar(prohort, ceagesp, colubande, f"{a.saida}/precos_comparativos.json")

    print("\nResumo (média 28 dias, Prohort):")
    for f in doc["frutas"]:
        pr = f["pracas"]
        if REFERENCIA in pr:
            linha = f"  {f['nome']:<10} RJ {pr[REFERENCIA]['media_28d']}"
            for k, v in f["comparacao_vs_rj"].items():
                linha += f" | {k} {pr[k]['media_28d']} ({v:+d}%)"
            print(linha)


if __name__ == "__main__":
    main()
