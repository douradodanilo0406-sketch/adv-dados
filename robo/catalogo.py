"""
Catálogo único de itens (config/itens.json) — a única fonte de verdade sobre QUAIS itens o robô
acompanha e COMO cada um aparece em cada fonte. Os coletores importam daqui.
"""
import csv, json, os, re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.environ.get("ADV_CATALOGO", os.path.join(RAIZ, "config", "itens.json"))
ARQ_SAZ = os.path.join(RAIZ, "base", "sazonalidade_ceagesp.csv")
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
PICO_MIN, ENTRESSAFRA_MAX = 70, 20   # nota de volume CEAGESP (0–100)


def _ler():
    with open(ARQ, encoding="utf-8") as f:
        doc = json.load(f)
    ids = [i["id"] for i in doc["itens"]]
    if len(ids) != len(set(ids)):
        raise ValueError("config/itens.json: id repetido")
    return doc


DOC = _ler()
TODOS = DOC["itens"]
ITENS = [i for i in TODOS if i.get("ativo", True)]
POR_NOME = {i["nome"]: i for i in ITENS}


def prohort_de(item):
    return [v["prohort"] for v in item["variedades"] if v.get("prohort")]


def referencia_prohort(item):
    p = prohort_de(item)
    return p[0] if p else None


def grupos_ceagesp():
    return tuple(sorted({i.get("grupo", "FRUTAS") for i in ITENS}))


def ceagesp_mapa():
    return [(i["nome"], i["ceagesp"]) for i in ITENS if i.get("ceagesp")]


def _sazonalidade():
    if not os.path.exists(ARQ_SAZ):
        return {}
    out = {}
    with open(ARQ_SAZ, encoding="utf-8") as f:
        for x in csv.DictReader(f):
            out[(x["produto"].strip(), x["variedade"].strip())] = [
                int(float(x[m])) if x[m] not in ("", None) else None for m in MESES]
    return out


SAZ = _sazonalidade()


def oferta_ceagesp(item):
    """Volume de entrada no CEAGESP (0–100) por mês da variedade de referência, ou None."""
    for v in item["variedades"]:
        chave = tuple(v.get("sazonalidade_ceagesp") or ())
        if chave and chave in SAZ:
            return SAZ[chave]
    return None


def suavizar(serie):
    """Média móvel de 3 meses (circular) — tira o ruído mês a mês da tabela de cores."""
    if not serie:
        return None
    out = []
    for m in range(12):
        viz = [serie[(m + d) % 12] for d in (-1, 0, 1) if serie[(m + d) % 12] is not None]
        out.append(round(sum(viz) / len(viz)) if viz and serie[m] is not None else None)
    return out


def safra(item):
    """Calendário de safra: o de referência (Cepea/Conab) ou, se não houver, o volume do CEAGESP."""
    if item.get("safra"):
        return item["safra"]
    o = suavizar(oferta_ceagesp(item))
    if not o:
        return None
    return {"pico": [m + 1 for m, n in enumerate(o) if n is not None and n >= PICO_MIN],
            "entressafra": [m + 1 for m, n in enumerate(o) if n is not None and n <= ENTRESSAFRA_MAX],
            "fonte": "CEAGESP — volume de entrada 2023–2025",
            "obs": "Pelo volume que chega ao CEAGESP (SP)"}


def frutas_legado():
    """Formato antigo usado pelo coletor_flv: nome -> (produto PAM, tabela PAM, produtos Prohort, NCMs)."""
    return {i["nome"]: ((i.get("pam") or {}).get("produto"), (i.get("pam") or {}).get("tabela"),
                        prohort_de(i), i.get("ncm") or []) for i in ITENS}


def safra_legado():
    return {i["nome"]: s for i in ITENS if (s := safra(i))}


def calendario_confirmado(mensal, ref):
    """O mês mais caro na CEASA-RJ cai na entressafra (ou colado nela)? None = não dá para testar."""
    if not mensal or not ref or not ref.get("entressafra"):
        return None
    pmax = max(mensal, key=lambda x: x["preco"])["mes"]
    return any(((pmax - 1 + d) % 12) + 1 in ref["entressafra"] for d in (-1, 0, 1))
