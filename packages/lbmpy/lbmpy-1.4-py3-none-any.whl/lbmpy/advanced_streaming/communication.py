import itertools
from pystencils import CreateKernelConfig, Field, Assignment, AssignmentCollection, Target
from pystencils.slicing import (
    shift_slice,
    get_slice_before_ghost_layer,
    normalize_slice,
)
from lbmpy.advanced_streaming.utility import (
    is_inplace,
    get_accessor,
    numeric_index,
    Timestep,
    get_timesteps,
    numeric_offsets,
)
from pystencils.datahandling import SerialDataHandling
from itertools import chain


class LBMPeriodicityHandling:

    def __init__(
        self,
        stencil,
        data_handling,
        pdf_field_name,
        streaming_pattern="pull",
        ghost_layers=1,
        cupy_direct_copy=True,
    ):
        """
        Periodicity Handling for Lattice Boltzmann Streaming.

        **On the usage with cuda:**
        - cupy allows the copying of sliced arrays within device memory using the numpy syntax,
        e.g. `dst[:,0] = src[:,-1]`. In this implementation, this is the default for periodicity
        handling. Alternatively, if you set `cupy_direct_copy=False`, GPU kernels are generated and
        compiled. The compiled kernels are almost twice as fast in execution as cupy array copying,
        but especially for large stencils like D3Q27, their compilation can take up to 20 seconds.
        Choose your weapon depending on your use case.
        """
        if not isinstance(data_handling, SerialDataHandling):
            raise ValueError("Only serial data handling is supported!")

        self.stencil = stencil
        self.dim = stencil.D
        self.dh = data_handling

        assert data_handling.default_target in [Target.CPU, Target.GPU]
        self.target = data_handling.default_target

        self.pdf_field_name = pdf_field_name
        self.ghost_layers = ghost_layers
        self.periodicity = data_handling.periodicity
        self.inplace_pattern = is_inplace(streaming_pattern)

        self.cpu = self.target == Target.CPU
        self.cupy_direct_copy = self.target == Target.GPU and cupy_direct_copy

        def is_copy_direction(direction):
            s = 0
            for d, p in zip(direction, self.periodicity):
                s += abs(d)
                if d != 0 and not p:
                    return False

            return s != 0

        full_stencil = itertools.product(*([-1, 0, 1] for _ in range(self.dim)))
        copy_directions = tuple(filter(is_copy_direction, full_stencil))
        self.comm_slices = []
        timesteps = get_timesteps(streaming_pattern)
        for timestep in timesteps:
            slices_per_comm_dir = get_communication_slices(
                stencil=stencil,
                comm_stencil=copy_directions,
                streaming_pattern=streaming_pattern,
                prev_timestep=timestep,
                ghost_layers=ghost_layers,
            )
            self.comm_slices.append(
                list(chain.from_iterable(v for k, v in slices_per_comm_dir.items()))
            )

        if self.target == Target.GPU and not cupy_direct_copy:
            self.device_copy_kernels = list()
            for timestep in timesteps:
                self.device_copy_kernels.append(self._compile_copy_kernels(timestep))

    def __call__(self, prev_timestep=Timestep.BOTH):
        if self.cpu:
            self._periodicity_handling_cpu(prev_timestep)
        else:
            self._periodicity_handling_gpu(prev_timestep)

    def _periodicity_handling_cpu(self, prev_timestep):
        arr = self.dh.cpu_arrays[self.pdf_field_name]
        comm_slices = self.comm_slices[prev_timestep.idx]
        for src, dst in comm_slices:
            arr[dst] = arr[src]

    def _compile_copy_kernels(self, timestep):
        assert self.target == Target.GPU
        pdf_field = self.dh.fields[self.pdf_field_name]
        kernels = []
        for src, dst in self.comm_slices[timestep.idx]:
            kernels.append(periodic_pdf_gpu_copy_kernel(pdf_field, src, dst))
        return kernels

    def _periodicity_handling_gpu(self, prev_timestep):
        arr = self.dh.gpu_arrays[self.pdf_field_name]
        if self.cupy_direct_copy:
            for src, dst in self.comm_slices[prev_timestep.idx]:
                arr[dst] = arr[src]
        else:
            kernel_args = {self.pdf_field_name: arr}
            for kernel in self.device_copy_kernels[prev_timestep.idx]:
                kernel(**kernel_args)


def get_communication_slices(
    stencil,
    comm_stencil=None,
    streaming_pattern="pull",
    prev_timestep=Timestep.BOTH,
    ghost_layers=1,
):
    """
    Return the source and destination slices for periodicity handling or communication between blocks.

    :param stencil: The stencil used by the LB method.
    :param comm_stencil: The stencil defining the communication directions. If None, it will be set to the
                         full stencil (D2Q9 in 2D, D3Q27 in 3D, etc.).
    :param streaming_pattern: The streaming pattern.
    :param prev_timestep: Timestep after which communication is run.
    :param ghost_layers: Number of ghost layers in each direction.

    """

    if comm_stencil is None:
        comm_stencil = itertools.product(*([-1, 0, 1] for _ in range(stencil.D)))

    pdfs = Field.create_generic(
        "pdfs", spatial_dimensions=len(stencil[0]), index_shape=(stencil.Q,)
    )
    write_accesses = get_accessor(streaming_pattern, prev_timestep).write(pdfs, stencil)
    slices_per_comm_direction = dict()

    for comm_dir in comm_stencil:
        if all(d == 0 for d in comm_dir):
            continue

        slices_for_dir = []

        for streaming_dir in set(_extend_dir(comm_dir)) & set(stencil):
            d = stencil.index(streaming_dir)
            write_index = numeric_index(write_accesses[d])[0]

            origin_slice = get_slice_before_ghost_layer(
                comm_dir, ghost_layers=ghost_layers, thickness=1
            )
            src_slice = _fix_length_one_slices(origin_slice)

            write_offsets = numeric_offsets(write_accesses[d])
            tangential_dir = tuple(s - c for s, c in zip(streaming_dir, comm_dir))

            # TODO: this is just a hotfix. _trim_slice_in_direction breaks FreeSlip BC with adjacent periodic side
            if streaming_pattern != "pull":
                src_slice = shift_slice(
                    _trim_slice_in_direction(src_slice, tangential_dir), write_offsets
                )

            neighbour_transform = _get_neighbour_transform(comm_dir, ghost_layers)
            dst_slice = shift_slice(src_slice, neighbour_transform)

            src_slice = src_slice + (write_index,)
            dst_slice = dst_slice + (write_index,)

            slices_for_dir.append((src_slice, dst_slice))

        slices_per_comm_direction[comm_dir] = slices_for_dir
    return slices_per_comm_direction


def periodic_pdf_gpu_copy_kernel(pdf_field, src_slice, dst_slice, domain_size=None):
    """Generate a GPU kernel which copies all values from one slice of a field
    to another non-overlapping slice."""
    from pystencils import create_kernel

    pdf_idx = src_slice[-1]
    assert isinstance(pdf_idx, int), "PDF index needs to be an integer constant"
    assert pdf_idx == dst_slice[-1], "Source and Destination PDF indices must be equal"
    src_slice = src_slice[:-1]
    dst_slice = dst_slice[:-1]

    # TODO this is the domain_size with GL
    if domain_size is None:
        domain_size = pdf_field.spatial_shape

    normalized_from_slice = normalize_slice(src_slice, domain_size)
    normalized_to_slice = normalize_slice(dst_slice, domain_size)

    def _start(s):
        return s.start if isinstance(s, slice) else s

    def _stop(s):
        return s.stop if isinstance(s, slice) else s

    offset = [
        _start(s1) - _start(s2)
        for s1, s2 in zip(normalized_from_slice, normalized_to_slice)
    ]
    assert offset == [
        _stop(s1) - _stop(s2)
        for s1, s2 in zip(normalized_from_slice, normalized_to_slice)
    ], "Slices have to have same size"

    copy_eq = AssignmentCollection(
        main_assignments=[
            Assignment(pdf_field(pdf_idx), pdf_field[tuple(offset)](pdf_idx))
        ]
    )
    config = CreateKernelConfig(
        iteration_slice=dst_slice,
        skip_independence_check=True,
        target=Target.GPU,
    )

    ast = create_kernel(copy_eq, config=config)
    return ast.compile()


def _extend_dir(direction):
    if len(direction) == 0:
        yield tuple()
    elif direction[0] == 0:
        for d in [-1, 0, 1]:
            for rest in _extend_dir(direction[1:]):
                yield (d,) + rest
    else:
        for rest in _extend_dir(direction[1:]):
            yield (direction[0],) + rest


def _get_neighbour_transform(direction, ghost_layers):
    return tuple(d * (ghost_layers + 1) for d in direction)


def _fix_length_one_slices(slices):
    """Slices of length one are replaced by their start value for correct periodic shifting"""
    if isinstance(slices, int):
        return slices
    elif isinstance(slices, slice):
        if slices.stop is not None and abs(slices.start - slices.stop) == 1:
            return slices.start
        elif slices.stop is None and slices.start == -1:
            return -1  # [-1:] also has length one
        else:
            return slices
    else:
        return tuple(_fix_length_one_slices(s) for s in slices)


def _trim_slice_in_direction(slices, direction):
    assert len(slices) == len(direction)

    result = []
    for s, d in zip(slices, direction):
        if isinstance(s, int):
            result.append(s)
            continue
        start = s.start + 1 if d == -1 else s.start
        stop = s.stop - 1 if d == 1 else s.stop
        result.append(slice(start, stop, s.step))

    return tuple(result)
