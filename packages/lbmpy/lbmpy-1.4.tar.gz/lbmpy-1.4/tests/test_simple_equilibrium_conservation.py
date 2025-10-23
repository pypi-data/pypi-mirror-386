import numpy as np

from pystencils import Target, CreateKernelConfig
from lbmpy.creationfunctions import create_lb_function, LBMConfig
from lbmpy.enums import Method, Stencil
from lbmpy.stencils import LBStencil
import pytest


@pytest.mark.parametrize('target', [Target.CPU, Target.GPU])
@pytest.mark.parametrize('method', [Method.SRT, Method.MRT, Method.CENTRAL_MOMENT, Method.CUMULANT])
@pytest.mark.parametrize('compressible', [False, True])
@pytest.mark.parametrize('delta_equilibrium', [False, True])
def test_simple_equilibrium_conservation(target, method, compressible, delta_equilibrium):
    if target == Target.GPU:
        pytest.importorskip("cupy")

    if method == Method.SRT and not delta_equilibrium:
        pytest.skip()

    if method == Method.CUMULANT and (not compressible or delta_equilibrium):
        pytest.skip()

    src = np.zeros((3, 3, 9))
    dst = np.zeros_like(src)
    config = CreateKernelConfig(target=target)
    lbm_config = LBMConfig(stencil=LBStencil(Stencil.D2Q9), method=method,
                           relaxation_rate=1.8, compressible=compressible,
                           zero_centered=True, delta_equilibrium=delta_equilibrium)
    func = create_lb_function(lbm_config=lbm_config, config=config)

    if target == Target.GPU:
        import cupy
        gpu_src, gpu_dst = cupy.asarray(src), cupy.asarray(dst)
        func(src=gpu_src, dst=gpu_dst)
        src[:] = gpu_src.get()
        dst[:] = gpu_dst.get()
    else:
        func(src=src, dst=dst)

    np.testing.assert_allclose(np.sum(np.abs(dst)), 0.0, atol=1e-13)
