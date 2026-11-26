"""Testes do catálogo (config/itens.json) — barram erro de digitação antes de publicar."""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "robo"))
import catalogo as c  # noqa: E402

CAMPOS = {"id", "nome", "grupo", "unidade", "variedades", "ceagesp", "pam", "ncm", "safra"}


def test_campos_e_ids():
    ids = [i["id"] for i in c.TODOS]
    assert len(ids) == len(set(ids))
    for i in c.TODOS:
        assert CAMPOS <= set(i), f"{i.get('id')}: faltam {CAMPOS - set(i)}"
        assert re.fullmatch(r"[a-z0-9-]+", i["id"]), i["id"]
        assert i["variedades"], f"{i['id']}: sem variedades"
        assert i["unidade"] in ("KG", "UN", "DZ", "MC", "CX"), i["id"]


def test_expressoes_ceagesp_validas():
    for nome, rx in c.ceagesp_mapa():
        re.compile(rx)


def test_ncm_8_digitos():
    for i in c.TODOS:
        for n in i["ncm"]:
            assert re.fullmatch(r"\d{8}", n), f"{i['id']}: NCM {n}"


def test_sazonalidade_ligada():
    for i in c.ITENS:
        assert c.oferta_ceagesp(i) is not None, f"{i['id']}: variedade sem par na tabela de volume CEAGESP"


def test_safra_meses_validos():
    for i in c.ITENS:
        s = c.safra(i)
        assert s, f"{i['id']}: sem calendário"
        for m in s.get("pico", []) + s.get("entressafra", []):
            assert 1 <= m <= 12
        assert not set(s.get("pico", [])) & set(s.get("entressafra", [])), f"{i['id']}: pico e entressafra no mesmo mês"


def test_mapeamento_ceagesp_15_frutas():
    import coletor_precos_ceasas as cmp
    casos = {"LARANJA PERA": "Laranja", "LIMÃO TAITI": "Limão", "BANANA PRATA MG": "Banana",
             "CAQUI RAMA FORTE": "Caqui", "CAQUI IMP.": None, "MANGA TOMMY ATCKINS": "Manga",
             "UVA RUBI": "Uva", "MELÃO AMARELO": "Melão", "ABACAXI PÉROLA": "Abacaxi",
             "MAMÃO HAVAÍ": "Mamão", "MAÇÃ GALA": "Maçã", "MAÇÃ GALA IMP.": None,
             "TANGERINA PONCÃ": "Tangerina", "TANGERINA MURCOTE": "Tangerina", "GOIABA VERMELHA": "Goiaba",
             "MARACUJÁ AZEDO": "Maracujá", "MARACUJÁ DOCE": None, "ABACATE BREDA": "Abacate",
             "ABACATE AVOCADO/HASS/FUERTE": None, "MELANCIA": "Melancia", "MELANCIA BABY": None}
    for prod, esperado in casos.items():
        assert cmp._fruta_ceagesp(prod) == esperado, prod


def test_calendario_confirmado():
    ref = {"entressafra": [12, 1, 2, 3]}
    assert c.calendario_confirmado([{"mes": 1, "preco": 5}, {"mes": 8, "preco": 2}], ref) is True
    assert c.calendario_confirmado([{"mes": 4, "preco": 5}, {"mes": 8, "preco": 2}], ref) is True   # colado
    assert c.calendario_confirmado([{"mes": 7, "preco": 5}, {"mes": 1, "preco": 2}], ref) is False
    assert c.calendario_confirmado([], ref) is None


def test_exportacao_forte_so_quando_pesa():
    import gerar_adv_dados as g
    meses = [10] * 11 + [200]  # pico em dez
    assert g.exportacao_forte({"exportacao_mensal_t": meses, "producao": {"total_t": 10_000}}) is not None   # 3,1%
    assert g.exportacao_forte({"exportacao_mensal_t": meses, "producao": {"total_t": 600_000}}) is None      # 0,05%
