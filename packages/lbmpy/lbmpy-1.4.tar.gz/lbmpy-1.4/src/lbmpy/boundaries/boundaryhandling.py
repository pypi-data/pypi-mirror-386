from dataclasses import replace
import numpy as np

from pystencils import Assignment, CreateKernelConfig, create_kernel, Field, Target, FieldType
from pystencils.boundaries import BoundaryHandling
from pystencils.boundaries.createindexlist import numpy_data_type_for_boundary_object
from pystencils.simp import add_subexpressions_for_field_reads
from pystencils.stencil import inverse_direction

from lbmpy.advanced_streaming.indexing import BetweenTimestepsIndexing
from lbmpy.advanced_streaming.utility import is_inplace, Timestep, AccessPdfValues

from .._compat import IS_PYSTENCILS_2

if IS_PYSTENCILS_2:
    from pystencils.types import PsNumericType


class LatticeBoltzmannBoundaryHandling(BoundaryHandling):
    """
    Enables boundary handling for LBM simulations with advanced streaming patterns.
    For the in-place patterns AA and EsoTwist, two kernels are generated for a boundary
    object and the right one selected depending on the time step.
    """

    def __init__(self, lb_method, data_handling, pdf_field_name, streaming_pattern='pull',
                 name="boundary_handling", flag_interface=None, target=Target.CPU, openmp=False, **kwargs):
        self._lb_method = lb_method
        self._streaming_pattern = streaming_pattern
        self._inplace = is_inplace(streaming_pattern)
        self._prev_timestep = None
        super(LatticeBoltzmannBoundaryHandling, self).__init__(
            data_handling, pdf_field_name, lb_method.stencil,
            name, flag_interface, target=target, openmp=openmp,
            **kwargs
        )

    #   ------------------------- Overridden methods of pystencils.BoundaryHandling -------------------------

    @property
    def prev_timestep(self):
        return self._prev_timestep

    def __call__(self, prev_timestep=Timestep.BOTH, **kwargs):
        self._prev_timestep = prev_timestep
        super(LatticeBoltzmannBoundaryHandling, self).__call__(**kwargs)
        self._prev_timestep = None

    def add_fixed_steps(self, fixed_loop, **kwargs):
        if self._inplace:  # Fixed Loop can't do timestep selection
            raise NotImplementedError("Adding to fixed loop is currently not supported for inplace kernels")
        super(LatticeBoltzmannBoundaryHandling, self).add_fixed_steps(fixed_loop, **kwargs)

    def _add_boundary(self, boundary_obj, flag=None):
        if self._inplace:
            return self._add_inplace_boundary(boundary_obj, flag)
        else:
            return super(LatticeBoltzmannBoundaryHandling, self)._add_boundary(boundary_obj, flag)

    def _add_inplace_boundary(self, boundary_obj, flag=None):
        if boundary_obj not in self._boundary_object_to_boundary_info:
            sym_index_field = Field.create_generic('indexField', spatial_dimensions=1, field_type=FieldType.INDEXED,
                                                   dtype=numpy_data_type_for_boundary_object(boundary_obj, self.dim))

            ast_even = self._create_boundary_kernel(self._data_handling.fields[self._field_name], sym_index_field,
                                                    boundary_obj, Timestep.EVEN)
            ast_odd = self._create_boundary_kernel(self._data_handling.fields[self._field_name], sym_index_field,
                                                   boundary_obj, Timestep.ODD)
            kernels = [ast_even.compile(), ast_odd.compile()]
            if flag is None:
                flag = self.flag_interface.reserve_next_flag()
            boundary_info = self.InplaceStreamingBoundaryInfo(self, boundary_obj, flag, kernels)
            self._boundary_object_to_boundary_info[boundary_obj] = boundary_info
        return self._boundary_object_to_boundary_info[boundary_obj].flag

    def _create_boundary_kernel(self, symbolic_field, symbolic_index_field, boundary_obj, prev_timestep=Timestep.BOTH):
        if IS_PYSTENCILS_2:
            additional_args = {"default_dtype": self._default_dtype}
        else:
            additional_args = dict()
            
        return create_lattice_boltzmann_boundary_kernel(
            symbolic_field, symbolic_index_field, self._lb_method, boundary_obj,
            prev_timestep=prev_timestep, streaming_pattern=self._streaming_pattern,
            target=self._target, cpu_openmp=self._openmp, **additional_args)

    class InplaceStreamingBoundaryInfo(object):

        @property
        def kernel(self):
            prev_timestep = self._boundary_handling.prev_timestep
            if prev_timestep is None:
                raise Exception(
                    "The boundary kernel property was accessed while "
                    + "there was no boundary handling in progress.")
            return self._kernels[prev_timestep]

        def __init__(self, boundary_handling, boundary_obj, flag, kernels):
            self._boundary_handling = boundary_handling
            self.boundary_object = boundary_obj
            self.flag = flag
            self._kernels = kernels

    #   end class InplaceStreamingBoundaryInfo

    # ------------------------------ Force On Boundary ------------------------------------------------------------

    def force_on_boundary(self, boundary_obj, prev_timestep=Timestep.BOTH):
        from lbmpy.boundaries import NoSlip
        self.__call__(prev_timestep=prev_timestep)
        if isinstance(boundary_obj, NoSlip):
            return self._force_on_no_slip(boundary_obj, prev_timestep)
        else:
            return self._force_on_boundary(boundary_obj, prev_timestep)

    def _force_on_no_slip(self, boundary_obj, prev_timestep):
        dh = self._data_handling
        ff_ghost_layers = dh.ghost_layers_of_field(self.flag_interface.flag_field_name)
        method = self._lb_method
        stencil = np.array(method.stencil)
        result = np.zeros(self.dim)

        for b in dh.iterate(ghost_layers=ff_ghost_layers):
            obj_to_ind_list = b[self._index_array_name].boundary_object_to_index_list
            pdf_array = b[self._field_name]
            if boundary_obj in obj_to_ind_list:
                ind_arr = obj_to_ind_list[boundary_obj]
                acc = AccessPdfValues(self._lb_method.stencil,
                                      streaming_pattern=self._streaming_pattern, timestep=prev_timestep,
                                      streaming_dir='out')
                values = 2 * acc.collect_from_index_list(pdf_array, ind_arr)
                forces = stencil[ind_arr['dir']] * values[:, np.newaxis]
                result += forces.sum(axis=0)
        return dh.reduce_float_sequence(list(result), 'sum')

    def _force_on_boundary(self, boundary_obj, prev_timestep):
        dh = self._data_handling
        ff_ghost_layers = dh.ghost_layers_of_field(self.flag_interface.flag_field_name)
        method = self._lb_method
        stencil = np.array(method.stencil)
        inv_direction = np.array([method.stencil.index(inverse_direction(d))
                                  for d in method.stencil])
        result = np.zeros(self.dim)

        for b in dh.iterate(ghost_layers=ff_ghost_layers):
            obj_to_ind_list = b[self._index_array_name].boundary_object_to_index_list
            pdf_array = b[self._field_name]
            if boundary_obj in obj_to_ind_list:
                ind_arr = obj_to_ind_list[boundary_obj]
                inverse_ind_arr = ind_arr.copy()
                inverse_ind_arr['dir'] = inv_direction[inverse_ind_arr['dir']]
                acc_out = AccessPdfValues(self._lb_method.stencil,
                                          streaming_pattern=self._streaming_pattern, timestep=prev_timestep,
                                          streaming_dir='out')
                acc_in = AccessPdfValues(self._lb_method.stencil,
                                         streaming_pattern=self._streaming_pattern, timestep=prev_timestep.next(),
                                         streaming_dir='in')
                acc_fluid = acc_out if boundary_obj.inner_or_boundary else acc_in
                acc_boundary = acc_in if boundary_obj.inner_or_boundary else acc_out
                fluid_values = acc_fluid.collect_from_index_list(pdf_array, ind_arr)
                boundary_values = acc_boundary.collect_from_index_list(pdf_array, inverse_ind_arr)
                values = fluid_values + boundary_values
                forces = stencil[ind_arr['dir']] * values[:, np.newaxis]
                result += forces.sum(axis=0)

        return dh.reduce_float_sequence(list(result), 'sum')


# end class LatticeBoltzmannBoundaryHandling

def create_lattice_boltzmann_boundary_kernel(pdf_field, index_field, lb_method, boundary_functor,
                                             prev_timestep=Timestep.BOTH, streaming_pattern='pull',
                                             target=Target.CPU, force_vector=None, **kernel_creation_args):
    from .._compat import IS_PYSTENCILS_2

    indexing = BetweenTimestepsIndexing(
        pdf_field, lb_method.stencil, prev_timestep, streaming_pattern, np.int32, np.int32)

    dim = lb_method.stencil.D
    f_out, f_in = indexing.proxy_fields
    dir_symbol = indexing.dir_symbol
    inv_dir = indexing.inverse_dir_symbol

    if IS_PYSTENCILS_2:
        from pystencils.types.quick import SInt
        config = CreateKernelConfig(
            index_field=index_field,
            target=target,
            index_dtype=SInt(32),
            skip_independence_check=True,
            **kernel_creation_args
        )

        default_data_type: PsNumericType = config.get_option("default_dtype")

        if force_vector is None:
            force_vector_type = np.dtype([(f"F_{i}", default_data_type.numpy_dtype) for i in range(dim)], align=True)
            force_vector = Field.create_generic('force_vector', spatial_dimensions=1,
                                                dtype=force_vector_type, field_type=FieldType.INDEXED)

        boundary_assignments = boundary_functor(f_out, f_in, dir_symbol, inv_dir, lb_method, index_field, force_vector)
        boundary_assignments = indexing.substitute_proxies(boundary_assignments)

        if pdf_field.dtype != default_data_type:
            boundary_assignments = add_subexpressions_for_field_reads(boundary_assignments, data_type=default_data_type)

        elements: list[Assignment] = []

        index_arrs_node = indexing.create_code_node()
        elements += index_arrs_node.get_array_declarations()
        
        for node in boundary_functor.get_additional_code_nodes(lb_method)[::-1]:
            elements += node.get_array_declarations()
            
        elements += [Assignment(dir_symbol, index_field[0]('dir'))]
        elements += boundary_assignments.all_assignments

        kernel = create_kernel(elements, config=config)
        return kernel
    else:
        config = CreateKernelConfig(index_fields=[index_field], target=target, default_number_int="int32",
                                    skip_independence_check=True, **kernel_creation_args)

        default_data_type = config.data_type.default_factory()

        if force_vector is None:
            force_vector_type = np.dtype([(f"F_{i}", default_data_type.c_name) for i in range(dim)], align=True)
            force_vector = Field.create_generic('force_vector', spatial_dimensions=1,
                                                dtype=force_vector_type, field_type=FieldType.INDEXED)

        config = replace(config, index_fields=[index_field, force_vector])

        boundary_assignments = boundary_functor(f_out, f_in, dir_symbol, inv_dir, lb_method, index_field, force_vector)
        boundary_assignments = indexing.substitute_proxies(boundary_assignments)

        if pdf_field.dtype != default_data_type:
            boundary_assignments = add_subexpressions_for_field_reads(boundary_assignments, data_type=default_data_type)

        elements = [Assignment(dir_symbol, index_field[0]('dir'))]
        elements += boundary_assignments.all_assignments

        kernel = create_kernel(elements, config=config)

        #   Code Elements ahead of the loop
        index_arrs_node = indexing.create_code_node()
        for node in boundary_functor.get_additional_code_nodes(lb_method)[::-1]:
            kernel.body.insert_front(node)
        kernel.body.insert_front(index_arrs_node)
        return kernel
