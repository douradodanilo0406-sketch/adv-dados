#!/usr/bin/env python3
"""
Calibragem do robô AdV Dados — confere, item por item, se cada fonte está achando o produto certo.

    python robo/calibrar.py                 # relatório: CALIBRAGEM.md + publico/calibragem.json
    python robo/calibrar.py --sugerir CAJU  # para incluir item novo: mostra os nomes em cada fonte
                                            # e imprime um bloco pronto para colar em config/itens.json

O relatório roda sozinho no fim de cada coleta (GitHub Actions).
"""
import argparse, datetime as dt, json, os, re, sys, unicodedata
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import catalogo  # noqa: E402

P = lambda *a: os.path.join(RAIZ, *a)  # noqa: E731
MESES = catalogo.MESES
PRACAS = {"ceasa-rj": "RJ", "ceagesp-sp": "SP", "campinas": "Campinas"}


def sem_acento(t):
    return unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().upper().strip()


def ler_json(c):
    try:
        with open(c, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _csv(c):
    return pd.read_csv(c) if os.path.exists(c) else pd.DataFrame()


# ---------------------------------------------------------------- relatório
def calibrar():
    app = ler_json(P("publico", "adv-dados.json")) or {"frutas": []}
    app_id = {f["id"]: f for f in app["frutas"]}
    base = next((ler_json(P("base", x)) for x in sorted(os.listdir(P("base")), reverse=True)
                 if x.startswith("mapa_abastecimento_") and x.endswith(".json")), None) or {"frutas": []}
    base_id = {f["id"]: f for f in base["frutas"]}
    prohort = _csv(P("dados", "prohort_comparativo.csv"))
    ceag = _csv(P("dados", "ceagesp_capital.csv"))
    if len(ceag):
        sys.path.insert(0, AQUI)
        import coletor_precos_ceasas as cmp
        ceag["fruta"] = ceag.produto.map(cmp._fruta_ceagesp)
    resultado = []
    for item in catalogo.ITENS:
        r = {"id": item["id"], "nome": item["nome"], "checagens": [], "notas": []}
        ok = lambda nome, cond, det: r["checagens"].append({"nome": nome, "ok": bool(cond), "detalhe": det})  # noqa: E731
        a = app_id.get(item["id"], {})
        b = base_id.get(item["id"], {})

        # 1. Conab/Prohort — variedade de referência nas 3 praças
        ref = catalogo.referencia_prohort(item)
        if ref:
            pv = prohort[(prohort.produto_prohort == ref)] if len(prohort) else prohort
            det = []
            for k, n in PRACAS.items():
                s = pv[pv.praca == k] if len(pv) else pv
                det.append(f"{n} {s.data.nunique() if len(s) else 0} dias")
            nrj = pv[pv.praca == "ceasa-rj"].data.nunique() if len(pv) else 0
            ok("Conab: preço da variedade de referência", nrj >= 20, f"{ref}: " + ", ".join(det))
            for k, v in (a.get("pracas") or {}).items():
                if v.get("confianca") == "baixa":
                    r["notas"].append(f"Conab {PRACAS[k]}: {v['obs']}")
        else:
            r["notas"].append("A Conab não cota este item: sem comparação entre praças, só CEAGESP.")

        # 2. Base anual (sazonalidade de preço na CEASA-RJ)
        mensal = b.get("preco_mensal_ceasarj") or []
        rep = [MESES[x["mes"] - 1] for x in mensal if x.get("alerta_preco_repetido")]
        if ref:
            ok("Base anual: 12 meses de preço na CEASA-RJ", len(mensal) == 12, f"{len(mensal)} meses no ano-base {base.get('ano_base')}")
        if rep:
            r["notas"].append(f"Preço repetido o mês inteiro em {', '.join(rep)} (baixa confiança nesses meses)")

        # 3. Calendário de safra
        sf = catalogo.safra(item)
        ok("Calendário de safra", sf and (sf.get("pico") or sf.get("entressafra")),
           f"{(sf or {}).get('fonte', 'sem fonte')}: pico {[MESES[m - 1] for m in (sf or {}).get('pico', [])]}, "
           f"entressafra {[MESES[m - 1] for m in (sf or {}).get('entressafra', [])]}")
        if mensal and sf and sf.get("entressafra"):
            pmax = max(mensal, key=lambda x: x["preco"])["mes"]
            pmin = min(mensal, key=lambda x: x["preco"])["mes"]
            conf = catalogo.calendario_confirmado(mensal, sf)
            ok("Preço confirma o calendário (mais caro na entressafra)", conf,
               f"mais caro em {MESES[pmax - 1]}, mais barato em {MESES[pmin - 1]}"
               + ("" if conf else " — fora da entressafra: o app esconde o texto de safra e mostra 'padrão em investigação'"))
        if catalogo.oferta_ceagesp(item) is None:
            r["notas"].append("Sem ligação com a tabela de volume do CEAGESP (sazonalidade_ceagesp).")

        # 4. CEAGESP
        if item.get("ceagesp") and len(ceag):
            c = ceag[ceag.fruta == item["nome"]]
            ult = ceag.data.max()
            hoje = c[c.data == ult]
            prods = sorted(c.produto.unique())
            fora = dt.date.today().month in ((sf or {}).get("entressafra") or [])
            ok("CEAGESP: produto encontrado no boletim", len(c) > 0 or fora,
               ("fora de época agora (entressafra): normal não aparecer. " if not len(c) and fora else "") +
               f"{len(prods)} produto(s) no histórico; {len(hoje)} linha(s) no último boletim ({ult})" +
               (f": {', '.join(sorted(hoje.produto.unique()))}" if len(hoje) else ""))
            # candidatos parecidos que NÃO estão mapeados (exceto importados)
            raiz = sem_acento(item["nome"]).split()[0]
            cand = sorted({x for x in ceag.produto.unique() if sem_acento(x).split()[0] == raiz
                           and "IMP" not in x and x not in prods})
            if cand:
                r["notas"].append("No CEAGESP e fora do mapeamento (de propósito ou não): " + ", ".join(cand))

        # 5. Comparação entre praças
        vs = {PRACAS[k]: v.get("vs_rj_pct") for k, v in (a.get("pracas") or {}).items() if v.get("vs_rj_pct") is not None}
        if vs:
            grandes = {k: v for k, v in vs.items() if abs(v) >= 45}
            ok("Diferença entre praças dentro do esperado (< 45%)", not grandes,
               ", ".join(f"{k} {v:+d}%" for k, v in vs.items()))

        # 6. Produção e exportação
        prod = (b.get("producao") or {}).get("total_t")
        if item.get("pam"):
            ok("IBGE/PAM: produção encontrada", bool(prod), f"{prod:,} t".replace(",", ".") if prod else "não achou")
        if item.get("ncm"):
            e = b.get("exportacao_mensal_t") or []
            ok("Comex Stat: exportação encontrada", sum(e) > 0, f"{round(sum(e)):,} t no ano".replace(",", "."))

        # 7. O que o app mostra no mês atual
        m = dt.date.today().month
        ctx = (a.get("contexto_por_mes") or [{}] * 12)[m - 1]
        r["app_mes_atual"] = " · ".join(x for x in (ctx.get("faixa"), ctx.get("texto"), ctx.get("safra")) if x)
        r["status"] = "ok" if all(x["ok"] for x in r["checagens"]) else "atenção"
        resultado.append(r)
    return resultado


def escrever(resultado):
    agora = dt.datetime.now().strftime("%d/%m/%Y %H:%M")
    n_ok = sum(r["status"] == "ok" for r in resultado)
    l = [f"# Calibragem do robô — {n_ok} de {len(resultado)} itens sem pendência",
         "", f"Gerado em {agora}. Catálogo: `config/itens.json` ({len(catalogo.ITENS)} itens ativos). "
         "Este arquivo é refeito a cada coleta.", "",
         "| Item | Status | O que o app mostra neste mês |", "| :--- | :---: | :--- |"]
    for r in resultado:
        l.append(f"| {r['nome']} | {'ok' if r['status'] == 'ok' else '**atenção**'} | {r['app_mes_atual'] or '—'} |")
    for r in resultado:
        l += ["", f"## {r['nome']} — {r['status']}", ""]
        for c in r["checagens"]:
            l.append(f"- [{'x' if c['ok'] else ' '}] {c['nome']}: {c['detalhe']}")
        for n in r["notas"]:
            l.append(f"- Nota: {n}")
    with open(P("CALIBRAGEM.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(l) + "\n")
    with open(P("publico", "calibragem.json"), "w", encoding="utf-8") as f:
        json.dump({"gerado_em": agora, "itens": resultado}, f, ensure_ascii=False, indent=1)
    print(f"Calibragem: {n_ok}/{len(resultado)} sem pendência → CALIBRAGEM.md")


# ---------------------------------------------------------------- sugerir item novo
def sugerir(nome):
    alvo = sem_acento(nome)
    print(f"\n== Onde '{nome}' aparece em cada fonte ==")
    cache = os.environ.get("ADV_CACHE", os.path.expanduser("~/cache_prohort"))
    arq = os.path.join(cache, "ProhortDiario.txt")
    prohort_nomes = []
    if os.path.exists(arq):
        from coletor_flv import ler_prohort
        d = ler_prohort(arq, usecols=["dsc_ceasa", "dsc_produto", "sig_unidade_medida"])
        d = d[d.dsc_produto.map(sem_acento).str.contains(alvo, regex=False)]
        t = d.groupby(["dsc_produto", "sig_unidade_medida"]).dsc_ceasa.apply(
            lambda s: sum(x in s.values for x in ("CEASA/RJ - RIO DE JANEIRO", "CEAGESP - SAO PAULO", "CEASA/SP - CAMPINAS"))).reset_index()
        print("\nConab/Prohort (produto, unidade, nº das 3 praças que cotam):")
        for x in t.itertuples():
            print(f"   {x.dsc_produto:<28} {x.sig_unidade_medida:<4} {x.dsc_ceasa}/3")
            prohort_nomes.append(x.dsc_produto)
        if not len(t):
            print("   (nada) — a Conab não cota; o item fica só com CEAGESP")
    else:
        print(f"\n(Conab: baixe o ProhortDiario.txt em {cache} para ver os nomes)")
    ceag = _csv(P("dados", "ceagesp_capital.csv"))
    print("\nCEAGESP (boletim):")
    cc = sorted({x for x in ceag.produto.unique() if alvo in sem_acento(x)}) if len(ceag) else []
    print("   " + ("\n   ".join(cc) if cc else "(nada nos boletins guardados; pode ser fora de época ou outro grupo: LEGUMES/VERDURAS)"))
    saz = _csv(catalogo.ARQ_SAZ)
    print("\nTabela de volume CEAGESP (produto | variedade | grupo):")
    s = saz[saz.produto.map(sem_acento).str.contains(alvo, regex=False)] if len(saz) else saz
    for x in s.itertuples():
        print(f"   {x.produto} | {x.variedade if isinstance(x.variedade, str) else ''} | {x.grupo}")
    grupo = s.grupo.iloc[0] if len(s) else "FRUTAS"
    var = (s.variedade.iloc[0] if len(s) and isinstance(s.variedade.iloc[0], str) else "")
    bloco = {"id": re.sub(r"[^a-z0-9]+", "-", alvo.lower()).strip("-"), "nome": nome.title(), "ativo": False,
             "grupo": grupo, "unidade": "KG",
             "variedades": [{"nome": var.title() or "Comum", "prohort": prohort_nomes[0] if prohort_nomes else None,
                             "sazonalidade_ceagesp": [s.produto.iloc[0], var] if len(s) else None}],
             "ceagesp": f"^{alvo}", "pam": None, "ncm": [], "safra": None}
    print("\nBloco para colar em config/itens.json (revise; comece com ativo=false, rode, confira CALIBRAGEM.md e então ative):")
    print(json.dumps(bloco, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sugerir", metavar="NOME")
    a = ap.parse_args()
    if a.sugerir:
        sugerir(a.sugerir)
    else:
        escrever(calibrar())


if __name__ == "__main__":
    main()
