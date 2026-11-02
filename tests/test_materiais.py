import numpy as np
import pytest

from materiais.condutividade import Condutividade
from materiais.materiais import Materiais


def _condutividade(geo='esfera', k=(1.0, 2.0, 3.0)):
    c = Condutividade()
    c.geo = geo
    c.k11, c.k22, c.k33 = k
    return c


def test_condutividade_e_um_material():
    assert isinstance(Condutividade(), Materiais)


def test_tensor_K_e_diagonal_com_k11_k22_k33():
    c = _condutividade()
    K = c.tensorK()
    np.testing.assert_allclose(K, np.diag([1.0, 2.0, 3.0]))
    assert c.K is K


def test_tensor_S_para_esfera_e_um_terco_da_identidade():
    c = _condutividade()
    np.testing.assert_allclose(c.tensorS(), np.eye(3) / 3)


def test_calc_preenche_K_e_S():
    c = _condutividade()
    c.calc()
    np.testing.assert_allclose(c.K, np.diag([1.0, 2.0, 3.0]))
    np.testing.assert_allclose(c.S, np.eye(3) / 3)


@pytest.mark.parametrize('geo', ['cilindro', 'disco', None])
def test_tensor_S_levanta_erro_claro_para_geometria_nao_suportada(geo):
    c = _condutividade(geo=geo)
    with pytest.raises(NotImplementedError, match=str(geo)):
        c.tensorS()
    assert c.S is None


def test_definir_tipo_nao_e_sombreado_pelo_atributo_tipo():
    c = Condutividade()
    assert callable(c.definir_tipo)
    c.definir_tipo()
    assert c.matTipo == 'isotropico'


def test_materiais_inicia_atributos_vazios():
    m = Materiais()
    assert (m.id, m.tipo, m.geo, m.fk, m.matTipo) == (None, None, None, None, None)
