import pytest

import pystencils as ps
from lbmpy import Stencil, LBStencil, LBMConfig, Method, lattice_viscosity_from_relaxation_rate, \
    LatticeBoltzmannStep, pdf_initialization_assignments, ForceModel
from lbmpy.boundaries.boundaryconditions import WallFunctionBounce, NoSlip, FreeSlip
from lbmpy.boundaries.wall_function_models import SpaldingsLaw, LogLaw, MoninObukhovSimilarityTheory, MuskerLaw
from pystencils.slicing import slice_from_direction


@pytest.mark.parametrize('stencil', [Stencil.D3Q19, Stencil.D3Q27])
@pytest.mark.parametrize('wfb_type', ['wfb_i', 'wfb_ii', 'wfb_iii', 'wfb_iv'])
def test_wfb(stencil, wfb_type):
    stencil = LBStencil(stencil)
    periodicity = (True, False, True)
    domain_size = (30, 20, 15)
    dim = len(domain_size)

    omega = 1.1
    nu = lattice_viscosity_from_relaxation_rate(omega)

    # pressure gradient for laminar channel flow with u_max = 0.1
    ext_force_density = 0.1 * 2 * nu / ((domain_size[1] - 2) / 2) ** 2

    lbm_config = LBMConfig(stencil=stencil,
                           method=Method.SRT,
                           force_model=ForceModel.GUO,
                           force=(ext_force_density, 0, 0),
                           relaxation_rate=omega,
                           compressible=True)

    wall_north = NoSlip()
    normal = (0, 1, 0)

    # NO-SLIP

    lb_step_noslip = LatticeBoltzmannStep(domain_size=domain_size, periodicity=periodicity,
                                          lbm_config=lbm_config, compute_velocity_in_every_step=True)

    noslip = NoSlip()

    lb_step_noslip.boundary_handling.set_boundary(noslip, slice_from_direction('S', dim))
    lb_step_noslip.boundary_handling.set_boundary(wall_north, slice_from_direction('N', dim))

    # FREE-SLIP

    lb_step_freeslip = LatticeBoltzmannStep(domain_size=domain_size, periodicity=periodicity,
                                            lbm_config=lbm_config, compute_velocity_in_every_step=True)

    freeslip = FreeSlip(stencil=stencil, normal_direction=normal)

    lb_step_freeslip.boundary_handling.set_boundary(freeslip, slice_from_direction('S', dim))
    lb_step_freeslip.boundary_handling.set_boundary(wall_north, slice_from_direction('N', dim))

    # WFB

    lb_step_wfb = LatticeBoltzmannStep(domain_size=domain_size, periodicity=periodicity,
                                       lbm_config=lbm_config, compute_velocity_in_every_step=True)

    # pdf initialisation

    init = pdf_initialization_assignments(lb_step_wfb.method, 1.0, (0.025, 0, 0),
                                          lb_step_wfb.data_handling.fields[lb_step_wfb._pdf_arr_name].center_vector)

    config = ps.CreateKernelConfig(target=lb_step_wfb.data_handling.default_target, cpu_openmp=False)
    ast_init = ps.create_kernel(init, config=config)
    kernel_init = ast_init.compile()

    lb_step_wfb.data_handling.run_kernel(kernel_init)

    lb_step_wfb.data_handling.fill(lb_step_wfb.velocity_data_name, 0.025, value_idx=0, ghost_layers=True)

    def ref_vel_callback(boundary_data, **_):
        for cell in boundary_data.index_array:
            cell['ref_vel_0'] = 0.025
            cell['ref_vel_2'] = 0.0

    def ref_vel_callback_maronga(boundary_data, **kwargs):
        ref_vel_callback(boundary_data, **kwargs)
        for cell in boundary_data.index_array:
            cell['ref_vel_0_first_cell'] = 0.025
            cell['ref_vel_2_first_cell'] = 0.0

    # wfb arguments
    wfb_args = {
        'wfb_i': {'wall_function_model': SpaldingsLaw(viscosity=nu),
                  'weight_method': WallFunctionBounce.WeightMethod.GEOMETRIC_WEIGHT,
                  'reference_velocity': WallFunctionBounce.ReferenceVelocity.INSTANTANEOUS_VELOCITY,
                  'name': "wall"},
        'wfb_ii': {'wall_function_model': MuskerLaw(viscosity=nu),
                   'weight_method': WallFunctionBounce.WeightMethod.GEOMETRIC_WEIGHT,
                   'reference_velocity': WallFunctionBounce.ReferenceVelocity.MEAN_VELOCITY,
                   'reference_velocity_callback': ref_vel_callback,
                   'name': "wall"},
        'wfb_iii': {'wall_function_model': LogLaw(viscosity=nu),
                    'weight_method': WallFunctionBounce.WeightMethod.LATTICE_WEIGHT,
                    'reference_velocity': WallFunctionBounce.ReferenceVelocity.INSTANTANEOUS_VELOCITY,
                    'sampling_shift': 2},
        'wfb_iv': {'wall_function_model': MoninObukhovSimilarityTheory(z0=1e-2),
                   'weight_method': WallFunctionBounce.WeightMethod.LATTICE_WEIGHT,
                   'reference_velocity': WallFunctionBounce.ReferenceVelocity.FILTERED_VELOCITY,
                   'filter_width': 1e-5,
                   'reference_velocity_callback': ref_vel_callback_maronga,
                   'sampling_shift': 2,
                   'use_maronga_correction': True}
    }

    wall = WallFunctionBounce(lb_method=lb_step_wfb.method, normal_direction=normal,
                              velocity_field=lb_step_wfb.data_handling.fields[lb_step_wfb.velocity_data_name],
                              **wfb_args[wfb_type])

    lb_step_wfb.boundary_handling.set_boundary(wall, slice_from_direction('S', dim))
    lb_step_wfb.boundary_handling.set_boundary(wall_north, slice_from_direction('N', dim))

    # run cases

    timesteps = 4000
    lb_step_noslip.run(timesteps)
    lb_step_freeslip.run(timesteps)
    lb_step_wfb.run(timesteps)

    noslip_velocity = lb_step_noslip.velocity[domain_size[0] // 2, :, domain_size[2] // 2, 0]
    freeslip_velocity = lb_step_freeslip.velocity[domain_size[0] // 2, :, domain_size[2] // 2, 0]
    wfb_velocity = lb_step_wfb.velocity[domain_size[0] // 2, :, domain_size[2] // 2, 0]

    assert wfb_velocity[0] > noslip_velocity[0], f"WFB enforced velocity below no-slip velocity"
    assert wfb_velocity[0] < freeslip_velocity[0], f"WFB enforced velocity above free-slip velocity"
