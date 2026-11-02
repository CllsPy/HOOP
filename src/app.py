"""App Streamlit do HOOP. Rode da raiz do repositório: ``streamlit run src/app.py``."""
import matplotlib

matplotlib.use('Agg')

import streamlit as st

from ui import estado
from ui.componentes import mapa_de_etapas
from ui.paginas import analise, dados, relatorio
from ui.tema import aplicar_tema

PAGINAS = {'dados': dados.render, 'analise': analise.render, 'relatorio': relatorio.render}


def resumos_das_etapas(etapa: str) -> dict:
    """Resumos das etapas já percorridas; a etapa atual mostra a descrição padrão."""
    resultado = estado.resultado_atual()
    if resultado is None:
        return {}
    resumos = {'dados': estado.resumo_entrada(resultado.entrada),
               'analise': estado.resumo_leitura(estado.leitura_atual())}
    resumos.pop(etapa, None)
    return resumos


def main() -> None:
    st.set_page_config(page_title='HOOP', page_icon=':material/bubble_chart:', layout='wide')
    aplicar_tema()
    etapa = estado.etapa_atual()
    mapa_de_etapas(etapa, estado.etapas_liberadas(), resumos_das_etapas(etapa))
    PAGINAS[etapa]()


main()
