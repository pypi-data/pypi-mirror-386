import os

import matplotlib.pyplot as plt
import meshio  # type: ignore
import mpi4py.MPI as MPI
import pygmsh as pg  # type: ignore
from dolfinx.io import XDMFFile
from lxml import etree
from phifem.mesh_scripts import compute_tags_measures

from src.meshtagsplot import plot_mesh_tags

mesh_path = os.path.join("meshes")
lcar = 0.1
with pg.geo.Geometry() as geom:
    # Points
    p1 = geom.add_point([0.0, 0.0, 0.0], lcar)
    p2 = geom.add_point([0.5, 0.0, 0.0], lcar)
    p3 = geom.add_point([-0.5, 0.0, 0.0], lcar)

    # Lines
    c1 = geom.add_circle_arc(p2, p1, p3)
    c2 = geom.add_circle_arc(p3, p1, p2)

    # Suface
    lloop = geom.add_curve_loop([c1, c2])
    surf = geom.add_plane_surface(lloop)

    mesh = geom.generate_mesh(dim=2, algorithm=6)

mesh.points = mesh.points[:, :2]

for cell_block in mesh.cells:
    if cell_block.type == "triangle":
        triangle_cells = [("triangle", cell_block.data)]

meshio.write_points_cells(
    os.path.join(mesh_path, "disk.xdmf"), mesh.points, triangle_cells
)

# meshio and dolfinx use incompatible Grid names ("Grid" for meshio and "mesh" for dolfinx)
# the lines below change the Grid name from "Grid" to "mesh" to ensure the compatibility between meshio and dolfinx.
tree = etree.parse(os.path.join(mesh_path, "disk.xdmf"))
root = tree.getroot()

for grid in root.findall(".//Grid"):
    grid.set("Name", "mesh")

tree.write(
    os.path.join(mesh_path, "disk.xdmf"),
    pretty_print=True,
    xml_declaration=True,
    encoding="UTF-8",
)


# Outside cells touching inside cells
def levelset(x):
    return x[0] ** 2 + x[1] ** 2 - 0.125


with XDMFFile(MPI.COMM_WORLD, os.path.join(mesh_path, "disk.xdmf"), "r") as fi:
    mesh = fi.read_mesh()

cells_tags, facets_tags, _, _, _, _ = compute_tags_measures(
    mesh, levelset, 10, box_mode=True
)

cells_dict = {1: "inside", 2: "cut", 3: "outside"}
fig = plt.figure()
ax = fig.subplots()
plot_mesh_tags(mesh, cells_tags, ax, expression_levelset=levelset, leg_dict=cells_dict)
plt.savefig("cells_tags_disk_tri.png", dpi=500, bbox_inches="tight")
facets_dict = {1: "inside", 2: "cut", 3: "boundary in", 4: "boundary out", 5: "outside"}
fig = plt.figure()
ax = fig.subplots()
plot_mesh_tags(
    mesh,
    facets_tags,
    ax,
    linewidth=2.5,
    leg_dict=facets_dict,
)
plt.savefig("facets_tags_disk_tri.png", dpi=500, bbox_inches="tight")
