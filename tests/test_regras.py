"""Casos de teste da Etapa 2 (seção 5), aplicados ao cruzamento do robô. Rodar: python -m pytest tests"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "robo"))
import gerar_adv_dados as g  # noqa: E402

BASE = json.load(open(os.path.join(os.path.dirname(__file__), "..", "base", "mapa_abastecimento_2025.json"), encoding="utf-8"))
F = {f["id"]: dict(f, _ano_base=BASE["ano_base"]) for f in BASE["frutas"]}


def ctx(fruta, mes):
    return g.contexto_mes(F[fruta], mes)


def test_laranja_nov():
    c = ctx("laranja", 11)
    assert c["indice"] == 86 and c["faixa"] == "barato"
    assert c["texto"] == "Costuma subir 50% até jan"
    assert c["safra"] == "Entressafra começa em dez"


def test_laranja_abr():
    c = ctx("laranja", 4)
    assert c["indice"] == 118 and c["faixa"] == "caro"
    assert c["texto"] == "Costuma cair 27% até jul"
    assert c.get("safra") != "Em entressafra"


def test_limao_abr():
    c = ctx("limao", 4)
    assert c["indice"] == 77 and c["texto"] == "Costuma subir 32% até jun"
    assert c["safra"] == "Entressafra começa em mai"


def test_manga_abr():
    c = ctx("manga", 4)
    assert c["texto"] == "Costuma subir 53% até jun" and c["safra"] == "Entressafra começa em mai"


def test_melao_nov():
    c = ctx("melao", 11)
    assert c["texto"].startswith("Costuma cair 21% até dez")
    assert F["melao"]["sinais"]["calendario_confirmado_pelo_preco"] is False
    assert g.exportacao_forte(F["melao"])["meses"] == ["jan", "fev", "out", "nov", "dez"]


def test_goiaba_nov():
    c = ctx("goiaba", 11)
    assert c["texto"].startswith("Preço costuma ficar estável") and "safra" not in c


def test_caqui():
    for m in range(1, 13):
        assert ctx("caqui", m)["texto"] == "Sem cotação diária na CEASA-RJ"


def test_laranja_sem_exportacao_forte():
    assert g.exportacao_forte(F["laranja"]) is None


def test_rotulo():
    assert ctx("laranja", 1)["rotulo"] == "Estimativa · padrão de 2025"
