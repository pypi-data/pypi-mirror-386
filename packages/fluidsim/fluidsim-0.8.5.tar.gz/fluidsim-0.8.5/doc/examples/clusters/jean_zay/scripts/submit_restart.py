import sys
import glob
from pathlib import Path
from fluidjean_zay import cluster
from math import pi

# Parameters of the simulation
dir_path = "/gpfswork/rech/zmr/uey73qw/aniso/"
N = 100.0
Fh = 1.0 / N
Rb = 20.0
proj = "None"
nz = 160
nh = 4 * nz
add_time = 10.0
# nu_2 = 0.0
nu_4 = 7.986161163605753e-10
delta_angle = 0.2
period_save_spatiotemporal_spectra = 2 * pi / (4 * N)
type_fft = "'fluidfft.fft3d.mpi_with_fftwmpi3d'"

# Parameters of the job
nb_nodes = 1
nb_cores_per_node = cluster.nb_cores_per_node
nb_procs = nb_mpi_processes = nb_nodes * nb_cores_per_node
walltime = "11:55:00"

# Find the path of the simulation
dir_path += "ns3d.strat_polo_"
if proj == "poloidal":
    dir_path += "proj_"
dir_path += f"Fh{Fh:.3e}_Rb{Rb:.3g}_{nh:d}x{nh:d}x{nz:d}_*"
print(dir_path)
paths = sorted(glob.glob(dir_path))
path = paths[-1]
print(path)

# Restart
command = (
    f"fluidsim-restart {path} --add-to-t_end {add_time} "
    f"--new-dir-results "
    f"--merge-missing-params "
    f'--modify-params "'
    f"params.oper.type_fft = {type_fft}; "
    f"params.output.periods_save.spatiotemporal_spectra = {period_save_spatiotemporal_spectra}; "
    # f'params.nu_2 = {nu_2}; '
    f"params.nu_4 = {nu_4}; "
    f"params.forcing.tcrandom_anisotropic.delta_angle = {delta_angle}; "
    f'"'
)

print(f"submitting:\npython {command}")

cluster.submit_command(
    f"{command}",
    name_run=f"ns3d.strat_proj{proj}_Fh{Fh:.3e}_Rb{Rb:.3g}",
    nb_nodes=nb_nodes,
    nb_cores_per_node=nb_cores_per_node,
    nb_mpi_processes=nb_mpi_processes,
    omp_num_threads=1,
    ask=True,
    walltime=walltime,
    dependency="singleton",
)
