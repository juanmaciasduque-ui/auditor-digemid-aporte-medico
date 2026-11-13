"""
Pruebas para el Mini-Agente y Motor de Búsqueda Regulatorio DIGEMID.
"""

from core.agents.digemid_agent import DigemidAgent


def test_agent_search_regulations():
    agent = DigemidAgent()
    
    # Búsqueda por flujograma
    res_flujo = agent.search_regulations("flujograma")
    assert len(res_flujo) > 0
    assert any("016" in r["norma_codigo"] for r in res_flujo)

    # Búsqueda por ftalatos
    res_ftalatos = agent.search_regulations("ftalatos")
    assert len(res_ftalatos) > 0
    assert any("003" in r["norma_codigo"] for r in res_ftalatos)


def test_agent_generate_remediation_templates():
    agent = DigemidAgent()

    # Carta de fabricante Art. 126
    carta = agent.generate_solution_template("CARTA_FABRICANTE_ART126")
    assert "APORTE MÉDICO PERÚ S.A.C." in carta["texto_espanol"]
    assert "20610321268" in carta["texto_espanol"]
    assert "ACE MEDICAL DEVICES" in carta["texto_ingles_ace"]

    # Flujograma Art. 130
    flujo = agent.generate_solution_template("FLUJOGRAMA_ART130")
    assert "Extrusión" in flujo["texto_espanol"]
    assert "Esterilización" in flujo["texto_espanol"]


def test_agent_precedents():
    agent = DigemidAgent()
    precedents = agent.get_precedents_for_product("cateter")
    assert len(precedents) >= 2
    assert any("DM17365E" in p.registro_sanitario for p in precedents)
