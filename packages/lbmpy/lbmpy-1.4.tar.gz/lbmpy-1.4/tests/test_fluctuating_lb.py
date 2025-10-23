"""Tests velocity and stress fluctuations for thermalized LB"""

import pytest
import pystencils as ps

from lbmpy._compat import IS_PYSTENCILS_2

from pystencils import get_code_str

if IS_PYSTENCILS_2:
    pass
else:
    from pystencils.backends.simd_instruction_sets import get_supported_instruction_sets, get_vector_instruction_set
    from pystencils.cpu.cpujit import get_compiler_config

from pystencils.enums import Target

from lbmpy.creationfunctions import *
from lbmpy.forcemodels import Guo 
from lbmpy.macroscopic_value_kernels import macroscopic_values_setter
import numpy as np
from lbmpy.enums import Stencil
from lbmpy.moments import is_bulk_moment, is_shear_moment, get_order
from lbmpy.stencils import LBStencil


if not IS_PYSTENCILS_2:
    def _skip_instruction_sets_windows(instruction_sets):
        if get_compiler_config()["os"] == "windows":
            # skip instruction sets supported by the CPU but not by the compiler
            if "avx" in instruction_sets and (
                "/arch:avx2" not in get_compiler_config()["flags"].lower()
                and "/arch:avx512" not in get_compiler_config()["flags"].lower()
            ):
                instruction_sets.remove("avx")
            if (
                "avx512" in instruction_sets
                and "/arch:avx512" not in get_compiler_config()["flags"].lower()
            ):
                instruction_sets.remove("avx512")
        return instruction_sets
    
    INSTRUCTION_SETS = get_supported_instruction_sets()
else:
    INSTRUCTION_SETS = Target.available_vector_cpu_targets()


def single_component_maxwell(x1, x2, kT, mass):
    """Integrate the probability density from x1 to x2 using the trapezoidal rule"""
    x = np.linspace(x1, x2, 1000)

    try:
        trapezoid = np.trapezoid  # since numpy 2.0
    except AttributeError:
        trapezoid = np.trapz

    return trapezoid(np.exp(-mass * x**2 / (2.0 * kT)), x) / np.sqrt(
        2.0 * np.pi * kT / mass
    )


def rr_getter(moment_group):
    """Maps a group of moments to a relaxation rate (shear, bulk, even, odd)
    in the 4 relaxation time thermalized LB model
    """
    is_shear = [is_shear_moment(m, 3) for m in moment_group]
    is_bulk = [is_bulk_moment(m, 3) for m in moment_group]
    order = [get_order(m) for m in moment_group]
    assert min(order) == max(order)
    order = order[0]

    if order < 2:
        return [0] * len(moment_group)
    elif any(is_bulk):
        assert all(is_bulk)
        return [sp.Symbol("omega_bulk")] * len(moment_group)
    elif any(is_shear):
        assert all(is_shear)
        return [sp.Symbol("omega_shear")] * len(moment_group)
    elif order % 2 == 0:
        assert order > 2
        return [sp.Symbol("omega_even")] * len(moment_group)
    else:
        return [sp.Symbol("omega_odd")] * len(moment_group)


def second_order_moment_tensor_assignments(function_values, stencil, output_field):
    """Assignments for calculating the pressure tensor"""
    assert len(function_values) == len(stencil)
    dim = len(stencil[0])
    return [
        ps.Assignment(
            output_field(i, j),
            sum(c[i] * c[j] * f for f, c in zip(function_values, stencil)),
        )
        for i in range(dim)
        for j in range(dim)
    ]


def add_pressure_output_to_collision_rule(collision_rule, pressure_field):
    pressure_ouput = second_order_moment_tensor_assignments(
        collision_rule.method.pre_collision_pdf_symbols,
        collision_rule.method.stencil,
        pressure_field,
    )
    collision_rule.main_assignments = collision_rule.main_assignments + pressure_ouput


def get_fluctuating_lb(
    size=None,
    kT=None,
    omega_shear=None,
    omega_bulk=None,
    omega_odd=None,
    omega_even=None,
    rho_0=None,
    target=None,
    zero_centered: bool = False,
):
    # Parameters
    stencil = LBStencil(Stencil.D3Q19)

    # Setup data handling
    dh = ps.create_data_handling(
        (size,) * stencil.D, periodicity=True, default_target=target
    )
    src = dh.add_array("src", values_per_cell=stencil.Q, layout="f")
    dst = dh.add_array_like("dst", "src")
    rho = dh.add_array("rho", layout="f", latex_name="\\rho", values_per_cell=1)
    u = dh.add_array("u", values_per_cell=dh.dim, layout="f")
    pressure_field = dh.add_array(
        "pressure", values_per_cell=(3, 3), layout="f", gpu=target == Target.GPU
    )
    force_field = dh.add_array(
        "force", values_per_cell=stencil.D, layout="f", gpu=target == Target.GPU
    )

    # Method setup
    lbm_config = LBMConfig(
        stencil=stencil,
        method=Method.MRT,
        compressible=True,
        weighted=True,
        zero_centered=zero_centered,
        relaxation_rates=rr_getter,
        force_model=Guo(force=force_field.center_vector),
        fluctuating={"temperature": kT},
        kernel_type="collide_only",
    )

    lb_method = create_lb_method(lbm_config=lbm_config)
    lbm_config.lb_method = lb_method

    lbm_opt = LBMOptimisation(symbolic_field=src, cse_global=True)
    collision_rule = create_lb_collision_rule(
        lbm_config=lbm_config, lbm_optimisation=lbm_opt
    )

    # add_pressure_output_to_collision_rule(collision_rule, pressure_field)

    collision = create_lb_update_rule(
        collision_rule=collision_rule, lbm_config=lbm_config, lbm_optimisation=lbm_opt
    )
    stream = create_stream_pull_with_output_kernel(
        collision.method,
        src,
        dst,
        {"density": rho, "velocity": u, "moment2": pressure_field},
    )

    config = ps.CreateKernelConfig(cpu_openmp=False, target=dh.default_target)

    # Compile kernels
    stream_kernel = ps.create_kernel(stream, config=config).compile()
    collision_kernel = ps.create_kernel(collision, config=config).compile()

    sync_pdfs = dh.synchronization_function([src.name])

    # Initialization
    init = macroscopic_values_setter(
        collision.method,
        velocity=(0,) * dh.dim,
        pdfs=src.center_vector,
        density=rho_0
    )
    init_kernel = ps.create_kernel(init, ghost_layers=0).compile()

    dh.fill(rho.name, rho_0)
    dh.fill(u.name, np.nan, ghost_layers=True, inner_ghost_layers=True)
    dh.fill(u.name, 0)
    dh.fill(force_field.name, np.nan, ghost_layers=True, inner_ghost_layers=True)
    dh.fill(force_field.name, 0)
    dh.run_kernel(init_kernel)

    # time loop
    def time_loop(start, steps):
        dh.all_to_gpu()
        for i in range(start, start + steps):
            dh.run_kernel(
                collision_kernel,
                omega_shear=omega_shear,
                omega_bulk=omega_bulk,
                omega_odd=omega_odd,
                omega_even=omega_even,
                seed=42,
                time_step=i,
            )

            sync_pdfs()
            dh.run_kernel(stream_kernel)

            dh.swap(src.name, dst.name)
        return start + steps

    return dh, time_loop


@pytest.mark.parametrize(
    "zero_centered", [False, True], ids=["regular-storage", "zero-centered"]
)
@pytest.mark.parametrize(
    "domain_size", [8, 60]
)
def test_resting_fluid(zero_centered: bool, domain_size: int, target=Target.CPU):
    rho_0 = 0.86 
    kT = 4e-4
    L = [domain_size] * 3 
    dh, time_loop = get_fluctuating_lb(
        size=L[0],
        target=target,
        rho_0=rho_0,
        kT=kT,
        omega_shear=0.8,
        omega_bulk=0.5,
        omega_even=0.04,
        omega_odd=0.3,
        zero_centered=zero_centered,
    )

    # Test
    t = 0
    # warm up
    t = time_loop(t, 10)

    # Measurement
    for i in range(10):
        t = time_loop(t, 5)

        res_u = dh.gather_array("u").reshape((-1, 3))
        res_rho = dh.gather_array("rho").reshape((-1,))

        # mass conservationo
        # density per cell fluctuates, but toal mass is conserved
        np.testing.assert_allclose(np.mean(res_rho), rho_0, atol=3E-12)

        # momentum conservation
        momentum = np.dot(res_rho, res_u)
        np.testing.assert_allclose(momentum, [0, 0, 0], atol=1e-10)

        # temperature (fluctuates around pre-set kT)
        kinetic_energy = 1 / 2 * np.dot(res_rho, res_u * res_u) / np.prod(L)
        kT_tol = 0.075 *(16/domain_size)**(3/2) 
        np.testing.assert_allclose(kinetic_energy, [kT / 2] * 3, rtol=kT_tol)

        # velocity distribution
        v_hist, v_bins = np.histogram(
            res_u, bins=11, range=(-0.075, 0.075), density=True
        )

        # Calculate expected values from single
        v_expected = []
        for j in range(len(v_hist)):
            # Maxwell distribution
            res = (
                1.0
                / (v_bins[j + 1] - v_bins[j])
                * single_component_maxwell(v_bins[j], v_bins[j + 1], kT, rho_0)
            )
            v_expected.append(res)
        v_expected = np.array(v_expected)

        hist_tol_all = 0.75 *(16/domain_size)**(3/2)
        np.testing.assert_allclose(v_hist, v_expected, rtol=hist_tol_all)
        hist_tol_center = hist_tol_all/10
        remove = 3
        np.testing.assert_allclose(
            v_hist[remove:-remove], v_expected[remove:-remove], rtol=hist_tol_center
        )

        # pressure tensor against expressions from
        # Duenweg, Schiller, Ladd, https://arxiv.org/abs/0707.1581

        res_pressure = dh.gather_array("pressure").reshape((-1, 3, 3))

        c_s = np.sqrt(1 / 3)  # speed of sound

        # average of pressure tensor
        # Diagonal elements are rho c_s^22 +<u,u>. When the fluid is
        # thermalized, the expectation value of <u,u> = kT due to the
        # equi-partition theorem.
        p_av_expected = np.diag([rho_0 * c_s**2 + kT] * 3)
        pressure_atol = c_s**2 / 200 *(16/domain_size)**(3/2)
        np.testing.assert_allclose(
            np.mean(res_pressure, axis=0), p_av_expected, atol=pressure_atol)



@pytest.mark.parametrize(
    "zero_centered", [False, True], ids=["regular-storage", "zero-centered"]
)
@pytest.mark.parametrize(
    "domain_size", [8, 60]
)
def test_point_force(zero_centered: bool, domain_size: int, target=Target.CPU):
    """Test momentum balance for thermalized fluid with applied poitn forces"""
    rho_0 = 0.86
    kT = 4e-4
    L = [domain_size] * 3
    dh, time_loop = get_fluctuating_lb(
        size=L[0],
        target=target,
        rho_0=rho_0,
        kT=kT,
        omega_shear=0.8,
        omega_bulk=0.5,
        omega_even=0.8,
        omega_odd=0.8,
        zero_centered=zero_centered
    )

    # Test
    t = 0
    # warm up
    t = time_loop(t, 100)

    introduced_momentum = np.zeros(3)
    for i in range(100):
        point_force = 1e-2/domain_size**(3/2) * (np.random.random(3) - 0.5)
        introduced_momentum += point_force

        # Note that ghost layers are included in the indexing
        force_pos = np.random.randint(1, L[0] - 2, size=3)

        dh.cpu_arrays["force"][force_pos[0], force_pos[1], force_pos[2]] = point_force
        t = time_loop(t, 1)
        res_u = dh.gather_array("u").reshape((-1, 3))
        res_rho = dh.gather_array("rho").reshape((-1,))
        

        # mass conservation
        np.testing.assert_allclose(np.mean(res_rho), rho_0, atol=3E-12)

        # momentum conservation
        momentum = np.dot(res_rho, res_u)
        np.testing.assert_allclose(
            momentum, introduced_momentum + 0.5 * point_force, atol=1e-10
        )
        dh.cpu_arrays["force"][force_pos[0], force_pos[1], force_pos[2]] = np.zeros(3)


@pytest.mark.skipif(
    not INSTRUCTION_SETS, reason="No vector instruction sets supported"
)
@pytest.mark.parametrize("data_type", ("float32", "float64"))
@pytest.mark.parametrize("assume_aligned", (True, False))
@pytest.mark.parametrize("assume_inner_stride_one", (True, False))
@pytest.mark.parametrize("assume_sufficient_line_padding", (True, False))
@pytest.mark.xfail(IS_PYSTENCILS_2, reason="Vectorization for RNGs not implemented yet")
def test_vectorization(
    data_type, assume_aligned, assume_inner_stride_one, assume_sufficient_line_padding
):
    stencil = LBStencil(Stencil.D3Q19)
    pdfs, pdfs_tmp = ps.fields(
        f"pdfs({stencil.Q}), pdfs_tmp({stencil.Q}): {data_type}[3D]", layout="fzyx"
    )

    method = create_mrt_orthogonal(
        stencil=stencil, compressible=True, weighted=True, relaxation_rates=rr_getter
    )

    if IS_PYSTENCILS_2:
        seed = ps.TypedSymbol("seed", np.uint32)
        rng = ps.random.Philox("phil", data_type, seed)
        fluct_options = {
            "temperature": sp.Symbol("kT"),
            "rng": rng,
        }
    else:
        rng_node = (
            ps.rng.PhiloxTwoDoubles if data_type == "float64" else ps.rng.PhiloxFourFloats
        )
        fluct_options = {
            "temperature": sp.Symbol("kT"),
            "rng_node": rng_node,
            "block_offsets": tuple([0] * stencil.D),
        }

    lbm_config = LBMConfig(
        lb_method=method,
        fluctuating=fluct_options,
        compressible=True,
        zero_centered=False,
        stencil=method.stencil,
        kernel_type="collide_only",
    )
    lbm_opt = LBMOptimisation(
        cse_global=True, symbolic_field=pdfs, symbolic_temporary_field=pdfs_tmp
    )

    collision = create_lb_update_rule(lbm_config=lbm_config, lbm_optimisation=lbm_opt)

    if not IS_PYSTENCILS_2:
        instruction_sets = _skip_instruction_sets_windows(INSTRUCTION_SETS)
    else:
        instruction_sets = INSTRUCTION_SETS

    instruction_set = instruction_sets[-1]

    if IS_PYSTENCILS_2:
        config = ps.CreateKernelConfig()
        config.target = instruction_set
        config.default_dtype = data_type
        config.cpu.vectorize.enable = True
        config.cpu.vectorize.assume_aligned = assume_aligned
        config.cpu.vectorize.assume_inner_stride_one = assume_inner_stride_one
    else:
        config = ps.CreateKernelConfig(
            target=Target.CPU,
            data_type=data_type,
            default_number_float=data_type,
            cpu_vectorize_info={
                "instruction_set": instruction_set,
                "assume_aligned": assume_aligned,
                "assume_inner_stride_one": assume_inner_stride_one,
                "assume_sufficient_line_padding": assume_sufficient_line_padding,
            },
        )

    if not assume_inner_stride_one and "storeS" not in get_vector_instruction_set(
        data_type, instruction_set
    ):
        with pytest.warns(UserWarning) as pytest_warnings:
            ast = ps.create_kernel(collision, config=config)
            assert "Could not vectorize loop" in pytest_warnings[0].message.args[0]
    else:
        ast = ps.create_kernel(collision, config=config)
    ast.compile()
    code = get_code_str(ast)
    print(code)


@pytest.mark.parametrize("data_type", ("float32", "float64"))
@pytest.mark.parametrize("assume_aligned", (True, False))
@pytest.mark.parametrize("assume_inner_stride_one", (True, False))
@pytest.mark.parametrize("assume_sufficient_line_padding", (True, False))
@pytest.mark.skipif(IS_PYSTENCILS_2, reason="waLBerla block offsets feature unavailable")
def test_fluctuating_lb_issue_188_wlb(
    data_type, assume_aligned, assume_inner_stride_one, assume_sufficient_line_padding
):
    stencil = LBStencil(Stencil.D3Q19)
    temperature = sp.symbols("temperature")
    pdfs, pdfs_tmp = ps.fields(
        f"pdfs({stencil.Q}), pdfs_tmp({stencil.Q}): {data_type}[3D]", layout="fzyx"
    )

    rng_node = (
        ps.rng.PhiloxTwoDoubles if data_type == "float64" else ps.rng.PhiloxFourFloats
    )
    fluctuating = {
        "temperature": temperature,
        "block_offsets": "walberla",
        "rng_node": rng_node,
    }

    lbm_config = LBMConfig(
        stencil=stencil,
        method=Method.MRT,
        compressible=True,
        weighted=True,
        zero_centered=False,
        relaxation_rate=1.4,
        fluctuating=fluctuating,
    )
    lbm_opt = LBMOptimisation(
        symbolic_field=pdfs, symbolic_temporary_field=pdfs_tmp, cse_global=True
    )

    up = create_lb_update_rule(lbm_config=lbm_config, lbm_optimisation=lbm_opt)

    cpu_vectorize_info = {
        "instruction_set": "avx",
        "assume_inner_stride_one": True,
        "assume_aligned": True,
    }
    config = ps.CreateKernelConfig(
        target=ps.Target.CPU,
        data_type=data_type,
        default_number_float=data_type,
        cpu_vectorize_info=cpu_vectorize_info,
    )

    ast = create_kernel(up, config=config)
    code = ps.get_code_str(ast)

    # print(code)

    if data_type == "float32":
        assert "0.5f" in code
        assert "_mm256_mul_ps" in code
        assert "_mm256_sqrt_ps" in code
    else:
        assert "0.5f" not in code
        assert "_mm256_mul_pd" in code
        assert "_mm256_sqrt_pd" in code
