import os

import dolfinx as dfx
import matplotlib.pyplot as plt
import mpi4py.MPI as MPI
import numpy as np
from dolfinx.io import XDMFFile
from phifem.mesh_scripts import compute_tags_measures

from src.meshtagsplot import plot_mesh_tags

mesh_path = os.path.join("meshes")
lcar = 0.1
lcar = 0.1
mesh_corners = np.array([[-1.5, -1.5], [1.5, 1.5]])
nx = int(np.abs(mesh_corners[1, 0] - mesh_corners[0, 0]) / lcar)
ny = int(np.abs(mesh_corners[1, 1] - mesh_corners[0, 1]) / lcar)
cell_type = dfx.cpp.mesh.CellType.triangle
mesh = dfx.mesh.create_rectangle(MPI.COMM_WORLD, mesh_corners, [nx, ny], cell_type)

with XDMFFile(mesh.comm, os.path.join(mesh_path, "square_tri.xdmf"), "w") as of:
    of.write_mesh(mesh)


# Outside cells touching inside cells
def levelset(x):
    return x[0] ** 2 + (0.3 * x[1] + 0.1) ** 2 - 0.65


with XDMFFile(MPI.COMM_WORLD, os.path.join(mesh_path, "square_tri.xdmf"), "r") as fi:
    mesh = fi.read_mesh()

cells_tags, facets_tags, _, _, _, _ = compute_tags_measures(
    mesh, levelset, 10, box_mode=True
)

cells_dict = {1: "inside", 2: "cut", 3: "outside"}

fig = plt.figure()
ax = fig.subplots()
plot_mesh_tags(mesh, cells_tags, ax, expression_levelset=levelset, leg_dict=cells_dict)
plt.savefig("cells_tags_square_tri.png", dpi=500, bbox_inches="tight")

facets_dict = {1: "inside", 2: "cut", 3: "boundary in", 4: "boundary out", 5: "outside"}

fig = plt.figure()
ax = fig.subplots()
plot_mesh_tags(
    mesh,
    facets_tags,
    ax,
    expression_levelset=levelset,
    linewidth=1.5,
    leg_dict=facets_dict,
)
plt.savefig("facets_tags_square_tri.png", dpi=500, bbox_inches="tight")
