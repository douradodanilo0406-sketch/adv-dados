#!/usr/bin/env python3
"""
Robô AdV Dados — coleta, cruza, valida e publica o arquivo único que o app AdV baixa.

Fluxo de cada rodada (seg/qua/sex 07:00 pelo GitHub Actions, ou à mão):
  1. Base anual (sazonalidade, produção, exportação) — IBGE/PAM + Prohort + Comex Stat.
     Regenerada no máximo 1x a cada 30 dias (ou com --anual). Se falhar, mantém a anterior.
  2. Preços comparativos — Conab/Prohort (RJ, CEAGESP SP, Campinas) + boletim CEAGESP do dia.
     A cada rodada. Se uma fonte falhar, mantém o último dado bom dela.
  3. Cruzamento — textos prontos por fruta e por mês (o app só mostra).
  4. Validação — schema, preços > 0, variação absurda contra a rodada anterior.
  5. Publicação — publico/adv-dados.json, publico/status.json e historico/AAAA-MM-DD.json.

Uso:
    python robo/gerar_adv_dados.py                 # rodada normal
    python robo/gerar_adv_dados.py --anual         # força regenerar a base anual
    python robo/gerar_adv_dados.py --sem-prohort   # só CEAGESP (teste rápido)
"""
import argparse, datetime as dt, json, os, shutil, sys, traceback, unicodedata
from zoneinfo import ZoneInfo
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import coletor_flv as flv            # noqa: E402
import coletor_precos_ceasas as cmp  # noqa: E402
import catalogo                      # noqa: E402
import hashlib                       # noqa: E402

SCHEMA = "adv-dados/1.0"
TZ = ZoneInfo("America/Sao_Paulo")
AGORA = dt.datetime.now(TZ)
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
VARIACAO_MAX = 3.0   # preço novo > 4x ou < 1/4 do anterior = absurdo
P = lambda *a: os.path.join(RAIZ, *a)  # noqa: E731
log = flv.log


def sem_acento(t):
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper().strip()


def ler_json(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------- 1. base anual
def hash_catalogo():
    campos = [(i["id"], (i.get("pam") or {}).get("produto"), catalogo.prohort_de(i), i.get("ncm"))
              for i in catalogo.ITENS]
    return hashlib.sha1(json.dumps(campos, sort_keys=True).encode()).hexdigest()[:12]


def base_anual(ano, cache, forcar):
    caminho = P("base", f"mapa_abastecimento_{ano}.json")
    atual = ler_json(caminho)
    if atual and not forcar and atual.get("catalogo_hash") not in (None, hash_catalogo()):
        log("catálogo mudou (item novo ou mapeamento alterado): regenerando a base anual")
        forcar = True
    if atual and not forcar:
        idade = (AGORA.date() - dt.date.fromisoformat(atual["gerado_em"])).days
        if idade < 30:
            return atual, {"status": "ok", "gerado_em": atual["gerado_em"], "obs": "base reutilizada"}
    try:
        pam = flv.coletar_pam(ano)
        precos = flv.coletar_precos(ano, cache)
        exp = flv.coletar_exportacao(ano)
        tmp = caminho + ".tmp"
        doc = flv.exportar_app(ano, pam, precos, pd.DataFrame(), exp, tmp)
        doc["catalogo_hash"] = hash_catalogo()
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
        if len(doc["frutas"]) < min(10, len(catalogo.ITENS)) or not any(f["preco_mensal_ceasarj"] for f in doc["frutas"]):
            raise ValueError("base anual incompleta")
        os.replace(tmp, caminho)
        return doc, {"status": "ok", "gerado_em": doc["gerado_em"]}
    except Exception as e:  # mantém a anterior
        log(f"base anual FALHOU: {e}")
        traceback.print_exc()
        if not atual:
            raise
        return atual, {"status": "falhou", "gerado_em": atual["gerado_em"], "obs": str(e)[:200]}


# ---------------------------------------------------------------- 2. preços comparativos
def precos(cache, sem_prohort, dias=120):
    st = {}
    arq_p = P("dados", "prohort_comparativo.csv")
    prohort = pd.read_csv(arq_p) if os.path.exists(arq_p) else pd.DataFrame()
    if not sem_prohort:
        try:
            novo = cmp.coletar_prohort(cache, dias)
            if len(novo) < 100:
                raise ValueError(f"só {len(novo)} preços")
            prohort = novo; prohort.to_csv(arq_p, index=False)
            st["prohort"] = {"status": "ok", "dados_ate": str(prohort.data.max())}
        except Exception as e:
            log(f"Prohort FALHOU: {e}")
            st["prohort"] = {"status": "falhou", "obs": str(e)[:200],
                             "dados_ate": str(prohort.data.max()) if len(prohort) else None}
    else:
        st["prohort"] = {"status": "nao_rodou", "dados_ate": str(prohort.data.max()) if len(prohort) else None}

    arq_c = P("dados", "ceagesp_capital.csv")
    try:
        novo = cmp.coletar_ceagesp(("FRUTAS",))
        if not len(novo):
            raise ValueError("boletim vazio")
        ceagesp = cmp.acumular(novo, arq_c, ["data", "grupo", "produto", "classificacao"])
        ceagesp["fruta"] = ceagesp.produto.map(cmp._fruta_ceagesp)  # reaplica o catálogo atual ao histórico
        st["ceagesp"] = {"status": "ok", "dados_ate": str(ceagesp.data.max())}
    except Exception as e:
        log(f"CEAGESP FALHOU: {e}")
        ceagesp = pd.read_csv(arq_c) if os.path.exists(arq_c) else pd.DataFrame()
        if len(ceagesp):
            ceagesp["fruta"] = ceagesp.produto.map(cmp._fruta_ceagesp)
        st["ceagesp"] = {"status": "falhou", "obs": str(e)[:200],
                         "dados_ate": str(ceagesp.data.max()) if len(ceagesp) else None}
    return prohort, ceagesp, st


# ---------------------------------------------------------------- 3. cruzamento (regras da Etapa 2)
def faixa(indice):
    if indice <= 90: return "barato"
    if indice <= 109: return "normal"
    if indice <= 129: return "caro"
    return "muito caro"


def contexto_mes(f, m):
    """Textos prontos para o mês m (1–12). Regras da Etapa 2, seção 5."""
    mensal = {x["mes"]: x for x in f.get("preco_mensal_ceasarj") or []}
    ref = f.get("safra_referencia") or {}
    ano = f.get("_ano_base")
    out = {"mes": m, "rotulo": f"Estimativa · padrão de {ano}"}
    if m not in mensal:
        out["texto"] = "Sem cotação diária na CEASA-RJ"
        _safra(out, ref, m)
        return out
    atual = mensal[m]
    out["indice"] = atual["indice"]; out["faixa"] = faixa(atual["indice"])
    prox = [((m + i - 1) % 12) + 1 for i in (1, 2, 3)]
    prox = [p for p in prox if p in mensal]
    texto, usado = "Preço costuma ficar estável nos próximos meses", None
    if prox:
        pmax = max(prox, key=lambda p: mensal[p]["preco"]); pmin = min(prox, key=lambda p: mensal[p]["preco"])
        alta = mensal[pmax]["preco"] / atual["preco"] - 1
        queda = mensal[pmin]["preco"] / atual["preco"] - 1
        if alta >= 0.10:
            texto, usado = f"Costuma subir {round(alta * 100)}% até {MESES[pmax - 1]}", pmax
        elif queda <= -0.10:
            texto, usado = f"Costuma cair {round(-queda * 100)}% até {MESES[pmin - 1]}", pmin
    if atual.get("alerta_preco_repetido") or (usado and mensal[usado].get("alerta_preco_repetido")):
        texto += " (baixa confiança: preço repetido pela Conab)"
    out["texto"] = texto
    _safra(out, ref, m)
    return out


def _safra(out, ref, m):
    if not ref:
        return
    nxt = m % 12 + 1
    if m in ref.get("entressafra", []):
        out["safra"] = "Em entressafra"
    elif nxt in ref.get("entressafra", []):
        out["safra"] = f"Entressafra começa em {MESES[nxt - 1]}"
    elif m in ref.get("pico", []):
        out["safra"] = "Em safra"


def exportacao_forte(f):
    e = f.get("exportacao_mensal_t") or []
    if not e or sum(e) < 1000:
        return None
    media = sum(e) / 12
    meses = [MESES[i] for i, v in enumerate(e) if v >= 1.5 * media]
    if not meses:
        return None
    lista = ", ".join(meses[:-1]) + f" e {meses[-1]}" if len(meses) > 1 else meses[0]
    return {"meses": meses, "texto": f"Exportação forte em {lista}: concorrência pela fruta"}


LIMITE_DIF_PRACAS = 45  # % — acima disso, provável variedade/qualidade diferente entre praças


confirma_calendario = catalogo.calendario_confirmado


def _praca_app(v, vs=None):
    d = {"media_28d": v["media_28d"], "ultimo": v["ultimo"]["preco"], "data": v["ultimo"]["data"],
         "certeza": "oficial"}
    if v.get("confianca"):
        d["confianca"] = v["confianca"]; d["obs"] = v["obs"]
    if vs is not None:
        d["vs_rj_pct"] = vs
    return d


def cruzar(base, prohort, ceagesp):
    pc = cmp.exportar(prohort, ceagesp, pd.DataFrame(), os.devnull)  # reaproveita o cálculo do comparativo
    por_id = {x["id"]: x for x in pc["frutas"]}
    base_id = {x["id"]: x for x in base["frutas"]}
    frutas = []
    for item in catalogo.ITENS:
        f = dict(base_id.get(item["id"]) or {"id": item["id"], "nome": item["nome"]}, _ano_base=base["ano_base"])
        ref = catalogo.safra(item)
        mensal = f.get("preco_mensal_ceasarj") or []
        calendario_ok = confirma_calendario(mensal, ref)
        # calibragem: se o preço do Rio contradiz o calendário, o app NÃO mostra "Em safra"/"Entressafra"
        f["safra_referencia"] = None if calendario_ok is False else ref
        c = por_id.get(item["id"], {})
        aliases = {sem_acento(item["nome"])} | {sem_acento(p) for p in catalogo.prohort_de(item)}
        aliases |= {sem_acento(x["produto"]) for x in c.get("ceagesp_classificacoes", [])}
        pracas = {k: _praca_app(v, c.get("comparacao_vs_rj", {}).get(k)) for k, v in c.get("pracas", {}).items()}
        alertas = []
        exf = exportacao_forte(f)
        if exf:
            alertas.append({"tipo": "exportacao_forte", **exf})
        if calendario_ok is False:
            alertas.append({"tipo": "padrao_em_investigacao", "texto": "padrão em investigação",
                            "obs": "o preço na CEASA-RJ não segue o calendário de safra de referência"})
        grandes = [k for k, v in pracas.items() if abs(v.get("vs_rj_pct") or 0) >= LIMITE_DIF_PRACAS]
        if grandes:
            alertas.append({"tipo": "diferenca_grande_entre_pracas", "pracas": grandes,
                            "texto": "Diferença grande entre praças: pode ser variedade ou qualidade diferente"})
        oferta = catalogo.suavizar(catalogo.oferta_ceagesp(item))
        out = {
            "id": item["id"], "nome": item["nome"], "aliases": sorted(aliases),
            "unidade": c.get("unidade") or f.get("unidade_preco") or item.get("unidade"),
            "contexto_por_mes": [contexto_mes(f, m) for m in range(1, 13)],
            "sazonal": {"indice_mes": [next((x["indice"] for x in mensal if x["mes"] == m), None) for m in range(1, 13)],
                        "preco_mes": [next((x["preco"] for x in mensal if x["mes"] == m), None) for m in range(1, 13)],
                        "pico": (ref or {}).get("pico"), "entressafra": (ref or {}).get("entressafra"),
                        "obs": (ref or {}).get("obs"), "fonte_safra": (ref or {}).get("fonte"),
                        "calendario_confirmado": calendario_ok,
                        "oferta_ceagesp_mes": oferta},
            "producao": f.get("producao"),
            "exportacao_mensal_t": f.get("exportacao_mensal_t"),
            "variedade_referencia": c.get("variedade_referencia"),
            "pracas": pracas,
            "variedades": [{"nome": v["nome"], "pracas": {k: _praca_app(x) for k, x in v["pracas"].items()}}
                           for v in c.get("variedades", []) if len(c.get("variedades", [])) > 1],
            "ceagesp_hoje": [{k: x[k] for k in ("data", "produto", "classificacao", "menor", "comum", "maior")}
                             for x in c.get("ceagesp_classificacoes", [])],
            "alertas": alertas,
        }
        if item.get("obs"):
            out["obs"] = item["obs"]
        frutas.append(out)
    return frutas


# ---------------------------------------------------------------- 4. validação
def validar(frutas, anterior):
    avisos = []
    ant = {f["id"]: f for f in (anterior or {}).get("frutas", [])}
    for f in frutas:
        for k, v in list(f["pracas"].items()):
            p = v.get("media_28d")
            if not p or p <= 0:
                avisos.append(f"{f['id']}/{k}: preço inválido ({p}), removido"); del f["pracas"][k]; continue
            velho = ant.get(f["id"], {}).get("pracas", {}).get(k, {}).get("media_28d")
            if velho and (p / velho > 1 + VARIACAO_MAX or velho / p > 1 + VARIACAO_MAX):
                avisos.append(f"{f['id']}/{k}: variação absurda {velho} → {p}, mantido o anterior")
                f["pracas"][k] = ant[f["id"]]["pracas"][k]
        f["ceagesp_hoje"] = [x for x in f["ceagesp_hoje"]
                             if x["comum"] and x["comum"] > 0 and x["menor"] <= x["comum"] * 1.5 and x["maior"] >= x["comum"] / 1.5]
    minimo = min(10, len(catalogo.ITENS))
    if len(frutas) < minimo:
        raise ValueError(f"só {len(frutas)} itens — não publico")
    return avisos


# ---------------------------------------------------------------- 5. publicação
def publicar(doc, status):
    os.makedirs(P("publico"), exist_ok=True); os.makedirs(P("historico"), exist_ok=True)
    tmp = P("publico", "adv-dados.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    teste = ler_json(tmp)
    assert teste and teste["schema"] == SCHEMA and teste["frutas"]
    os.replace(tmp, P("publico", "adv-dados.json"))
    shutil.copy(P("publico", "adv-dados.json"), P("historico", f"{AGORA:%Y-%m-%d}.json"))
    with open(P("publico", "status.json"), "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=1)
    log(f"publicado: {os.path.getsize(P('publico', 'adv-dados.json')) // 1024} KB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano-base", type=int, default=2025)
    ap.add_argument("--cache", default=os.environ.get("ADV_CACHE", os.path.expanduser("~/cache_prohort")))
    ap.add_argument("--anual", action="store_true")
    ap.add_argument("--sem-prohort", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)

    base, st_base = base_anual(a.ano_base, a.cache, a.anual)
    prohort, ceagesp, st = precos(a.cache, a.sem_prohort)
    st["base_anual"] = st_base
    anterior = ler_json(P("publico", "adv-dados.json"))
    frutas = cruzar(base, prohort, ceagesp)
    avisos = validar(frutas, anterior)
    for x in avisos:
        log("AVISO " + x)

    doc = {
        "schema": SCHEMA, "versao": AGORA.isoformat(timespec="seconds"), "ano_base": base["ano_base"],
        "referencia": "ceasa-rj",
        "pracas": {"ceasa-rj": "CEASA-RJ (Irajá)", "ceagesp-sp": "CEAGESP São Paulo", "campinas": "CEASA Campinas"},
        "fontes": st,
        "legenda": {
            "contexto_por_mes": "Índice 0 = janeiro. Estimativa pelo padrão do ano-base; nunca é preço oficial.",
            "pracas": "Média de 28 dias, Conab/Prohort, R$/kg (abacaxi R$/unidade). vs_rj_pct = diferença % para a CEASA-RJ.",
            "ceagesp_hoje": "Boletim CEAGESP mais recente, R$/kg por classificação.",
        },
        "frutas": frutas,
    }
    publicar(doc, {"versao": doc["versao"], "fontes": st, "avisos": avisos})
    falhas = [k for k, v in st.items() if v["status"] == "falhou"]
    print("\nFontes:", {k: v["status"] for k, v in st.items()}, "| avisos:", len(avisos))
    if falhas:
        print("::warning::fontes com falha (mantido o último dado bom): " + ", ".join(falhas))


if __name__ == "__main__":
    main()
