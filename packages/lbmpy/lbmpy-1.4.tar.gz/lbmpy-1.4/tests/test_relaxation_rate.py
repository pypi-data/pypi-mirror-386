import pytest
import sympy as sp
from lbmpy.creationfunctions import create_lb_method, LBMConfig
from lbmpy.moments import is_shear_moment, get_order
from lbmpy.enums import Method, Stencil
from lbmpy.relaxationrates import get_shear_relaxation_rate
from lbmpy.stencils import LBStencil


def test_relaxation_rate():
    lbm_config = LBMConfig(stencil=LBStencil(Stencil.D3Q19), method=Method.MRT_RAW,
                           relaxation_rates=[1 + i / 10 for i in range(19)])
    method = create_lb_method(lbm_config=lbm_config)
    with pytest.raises(ValueError) as e:
        get_shear_relaxation_rate(method)
    assert 'Shear moments are relaxed with different relaxation' in str(e.value)

    omegas = sp.symbols("omega_:4")
    lbm_config = LBMConfig(stencil=LBStencil(Stencil.D3Q19), method=Method.MRT,
                           relaxation_rates=omegas)
    method = create_lb_method(lbm_config=lbm_config)
    assert get_shear_relaxation_rate(method) == omegas[0]


@pytest.mark.parametrize("method", [Method.MRT, Method.CENTRAL_MOMENT, Method.CUMULANT])
def test_default_mrt_behaviour(method):
    lbm_config = LBMConfig(stencil=LBStencil(Stencil.D3Q19), method=method, compressible=True)
    method = create_lb_method(lbm_config=lbm_config)

    for moment, relax_info in method.relaxation_info_dict.items():
        if get_order(moment) <= 1:
            assert relax_info.relaxation_rate == 0
        elif is_shear_moment(moment, method.dim):
            assert relax_info.relaxation_rate == sp.Symbol('omega')
        else:
            assert relax_info.relaxation_rate == 1
