#!/usr/bin/env python3
"""
Lê a tabela oficial "Sazonalidade de quantidade" do CEAGESP (PDF colorido) e grava uma nota de
volume de entrada por mês (0 = muito pouca mercadoria, 100 = muita mercadoria) para cada
produto/variedade. A cor de cada célula vai do verde (alto volume) ao vermelho (baixo volume);
célula branca = sem registro.

Uso (só quando o CEAGESP publicar uma tabela nova, cerca de 1x por ano):
    pip install pdfplumber
    python robo/ler_sazonalidade_ceagesp.py --pdf sazonalidade.pdf --periodo 2023-2025

Fonte: https://ceagesp.gov.br/sazonalidade/
Saída: base/sazonalidade_ceagesp.csv
"""
import argparse, colorsys, csv, os

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rgb(cor):
    if cor is None:
        return None
    if len(cor) == 4:  # CMYK
        c, m, y, k = cor
        return (1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k)
    if len(cor) == 3:
        return tuple(cor)
    if len(cor) == 1:
        return (cor[0],) * 3
    return None


def nota(cor):
    """Verde (matiz ~120°) = 100, amarelo (~60°) = 50, vermelho (0°) = 0. Branco/cinza = None."""
    rgb = _rgb(cor)
    if rgb is None:
        return None
    h, l, s = colorsys.rgb_to_hls(*rgb)
    if s < 0.25 or l > 0.92:
        return None
    graus = h * 360
    if graus > 200:  # tons de vermelho do lado "de lá" do círculo
        graus = 0
    return round(max(0, min(120, graus)) / 120 * 100)


def ler(pdf_path):
    import pdfplumber
    linhas = []
    with pdfplumber.open(pdf_path) as pdf:
        for pg in pdf.pages:
            palavras = pg.extract_words(keep_blank_chars=False)
            cab = {w["text"].lower(): w for w in palavras if w["text"].lower() in MESES}
            if len(cab) < 12:
                continue
            colunas = [((cab[m]["x0"] + cab[m]["x1"]) / 2) for m in MESES]
            hp = next(w for w in palavras if w["text"] == "PRODUTO")
            hn = next(w for w in palavras if w["text"] in ("N°", "Nº", "N"))
            hv = next(w for w in palavras if w["text"] == "VARIEDADE")
            # cabeçalhos são centralizados: borda = ponto médio entre os centros vizinhos
            c_n, c_p, c_v = [(h["x0"] + h["x1"]) / 2 for h in (hn, hp, hv)]
            x_meses = cab["jan"]["x0"] - 4
            x_prod = c_n + 10                      # produto começa logo depois do número
            x_var = c_v - (x_meses - c_v)          # variedade é centralizada entre sua borda e "jan"
            x_prod_min = x_prod
            grupos = [w for w in palavras if w["text"] in ("FRUTAS", "LEGUMES", "VERDURAS", "DIVERSOS", "FLORES", "PESCADOS", "OVOS")
                      and w["x0"] < x_prod_min - 20]
            retang = [r for r in pg.rects if r["width"] < 40 and r["height"] < 25]
            for g in grupos:
                topo, base = g["top"] - 1, g["bottom"] + 1
                meio = (g["top"] + g["bottom"]) / 2
                da_linha = [w for w in palavras if abs((w["top"] + w["bottom"]) / 2 - meio) < 3]
                produto = " ".join(w["text"] for w in da_linha if x_prod <= w["x0"] < x_var - 3)
                variedade = " ".join(w["text"] for w in da_linha if x_var - 3 <= w["x0"] < x_meses)
                notas = []
                for cx in colunas:
                    cel = [r for r in retang if r["x0"] - 1 <= cx <= r["x1"] + 1 and r["top"] - 2 <= meio <= r["bottom"] + 2]
                    notas.append(nota(cel[-1].get("non_stroking_color")) if cel else None)
                linhas.append({"grupo": g["text"], "produto": produto.strip(), "variedade": variedade.strip(),
                               **{m: n for m, n in zip(MESES, notas)}})
    return linhas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--periodo", default="2023-2025")
    ap.add_argument("--saida", default=os.path.join(RAIZ, "base", "sazonalidade_ceagesp.csv"))
    a = ap.parse_args()
    linhas = ler(a.pdf)
    with open(a.saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["grupo", "produto", "variedade", *MESES, "periodo", "fonte"])
        w.writeheader()
        for x in linhas:
            w.writerow({**x, "periodo": a.periodo, "fonte": "CEAGESP/SEDES — Sazonalidade de quantidade"})
    print(f"{len(linhas)} linhas → {a.saida}")


if __name__ == "__main__":
    main()
