import inspect

import struphy.post_processing.pproc_struphy as pproc_struphy
import struphy.propagators.propagators_coupling as propagators_coupling
import struphy.propagators.propagators_fields as propagators_fields
import struphy.propagators.propagators_markers as propagators_markers
from struphy.post_processing.likwid.plot_time_traces import (
    plot_gantt_chart,
    plot_gantt_chart_plotly,
    plot_time_vs_duration,
)
from struphy.utils.utils import subp_run


def struphy_pproc(
    dirs,
    dir_abs=None,
    step=1,
    celldivide=1,
    physical=False,
    guiding_center=False,
    classify=False,
    no_vtk=False,
    time_trace=[],
):
    """Post process data from finished Struphy runs.

    Parameters
    ----------
    dirs : str
        Paths of simulation output folders relative to <struphy_path>/io/out.

    dir_abs : str
        Absolute path to the simulation output folder.

    step : int, optional
        Whether to do post-processing at every time step (step=1, default), every second time step (step=2), etc.

    celldivide : int, optional
        Number of grid point in each cell used to create vtk files (default=1).

    physical : bool
        Wether to do post-processing into push-forwarded physical (xyz) components of fields.

    guiding_center : bool
        Compute guiding-center coordinates (only from Particles6D).

    classify : bool
        Classify guiding-center trajectories (passing, trapped or lost).
    """
    import os

    import struphy
    import struphy.utils.utils as utils

    # Read struphy state file
    libpath = struphy.__path__[0]
    state = utils.read_state(libpath)

    o_path = state["o_path"]

    use_state_o_path = True
    if dir_abs is not None:
        dirs = [dir_abs]
        use_state_o_path = False

    absolute_paths = []
    for dir in dirs:
        # create absolute path
        if use_state_o_path:
            absolute_paths.append(os.path.join(o_path, dir))
        else:
            absolute_paths.append(dir)

    for path_to_simulation in absolute_paths:
        print(f"Post processing data in {path_to_simulation}")

        command = [
            "python3",
            "post_processing/pproc_struphy.py",
            path_to_simulation,
            "-s",
            str(step),
            "--celldivide",
            str(celldivide),
        ]

        if physical:
            command += ["--physical"]

        if guiding_center:
            command += ["--guiding-center"]

        if classify:
            command += ["--classify"]

        # Whether vtk files should be created
        if no_vtk:
            command += ["--no-vtk"]

        subp_run(command)

    if len(time_trace) > 0:
        print(f"Plotting time trace for the following regions: {', '.join(time_trace)}")
        for path in absolute_paths:
            path_time_trace = os.path.join(path, "profiling_time_trace.pkl")
            if not os.path.isfile(path_time_trace):
                raise FileNotFoundError(f"No profiling time trace found at {path_time_trace}")

            # plot_time_vs_duration(path_time_trace, output_path=path_pproc)
            # plot_gantt_chart(path_time_trace, output_path=path_pproc)

            propagators = []
            for module in [propagators_coupling, propagators_markers, propagators_fields]:
                propagators += [
                    name
                    for name, obj in inspect.getmembers(module, inspect.isclass)
                    if obj.__module__ == module.__name__
                ]
            groups_include = time_trace

            if "kernels" in groups_include:
                groups_include += ["kernel:*"]
            if "propagators" in groups_include:
                groups_include += propagators

            plot_gantt_chart_plotly(
                path_time_trace,
                output_path=path,
                groups_include=groups_include,
                show=False,
            )
