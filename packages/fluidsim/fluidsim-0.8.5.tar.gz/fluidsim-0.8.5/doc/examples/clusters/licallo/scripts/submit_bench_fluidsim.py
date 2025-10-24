"""
submit_bench_fluidsim.py
===============

Script to run the benchmarks of fluidsim (Script to run the benchmarks of fluidsim (https://fluidsim.readthedocs.io/en/latest/test_bench_profile.html)
Once you have runned many runs, you can run fluidsim-bench-analysis

Exemple:
python submit_bench_fluidsim.py
cd /scratch/$USER/fluidsim_bench
fluidsim-bench-analysis 320 1280 1280 -i . -s ns3d.strat

"""

from fluidlicallo import cluster


def submit(nb_nodes):
    nb_cores_per_node = cluster.nb_cores_per_node
    nb_mpi = nb_nodes * nb_cores_per_node

    cluster.submit_command(
        "fluidsim-bench -s ns3d.strat 320 1280 1280 "
        "-o /scratch/$USER/fluidsim_bench "
        '-t "fft3d.mpi_with_fftw1d" '
        "-it 20",
        name_run=f"fluidsim-bench_320_1280_1280_{nb_mpi:02d}",
        nb_nodes=nb_nodes,
        nb_cores_per_node=nb_cores_per_node,
        walltime="02:00:00",
        nb_mpi_processes=nb_mpi,
        omp_num_threads=1,
        ask=False,
        delay_signal_walltime=None,
    )


for nb_nodes in [1, 2, 4, 8]:
    submit(nb_nodes)
