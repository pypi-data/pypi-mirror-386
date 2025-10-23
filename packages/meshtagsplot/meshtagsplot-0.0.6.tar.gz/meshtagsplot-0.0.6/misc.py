def plot_mesh(
    mesh: Any,
    bbox: npt.NDArray,
    ax: plt.Axes | None = None,
    expression_levelset: Callable[..., np.ndarray] | None = None,
) -> plt.Axes:
    """Plot a mesh.

    Args:
        mesh: the corresponding mesh.
        bbox: the domain bounding box.
        ax: (optional) the matplotlib axes.
        expression_levelset: (optional), if not None, display the contour line of the levelset.

    Returns:
        A matplotlib axis with the corresponding plot.
    """
    if ax is None:
        ax = plt.gca()  # type: ignore
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_xlim(bbox[0, 0], bbox[0, 1])
    ax.set_ylim(bbox[1, 0], bbox[1, 1])
    points = mesh.geometry.x

    mappable: mpl_collections.Collection

    cells = mesh.geometry.dofmap
    num_cells = cells.shape[0]
    tria = tri.Triangulation(points[:, 0], points[:, 1], cells)
    c = np.ones(num_cells)
    # create a colormap with a single color
    cmap = mcolors.ListedColormap("white")
    mappable = ax.tripcolor(
        tria, facecolors=c, edgecolor="k", linewidth=0.75, cmap=cmap
    )

    if expression_levelset is not None:
        x_min, x_max = np.min(points[:, 0]), np.max(points[:, 0])
        y_min, y_max = np.min(points[:, 1]), np.max(points[:, 1])
        nx = 1000
        ny = 1000
        xs = np.linspace(x_min, x_max, nx)
        ys = np.linspace(y_min, y_max, ny)

        xx, yy = np.meshgrid(xs, ys)
        xx_rs = xx.reshape(xx.shape[0] * xx.shape[1])
        yy_rs = yy.reshape(yy.shape[0] * yy.shape[1])
        points = np.vstack([xx_rs, yy_rs])
        zz_rs = expression_levelset(points)
        zz = zz_rs.reshape(xx.shape)

        ax.contour(xx, yy, zz, [0.0], linewidths=0.5)

    return ax


def plot_dg0_function(
    mesh: Any,
    function: Any,
    ax: plt.Axes | None = None,
    expression_levelset: Callable[..., np.ndarray] | None = None,
    vbounds: tuple = (-1.0, 1.0),
    label: str | None = None,
    cmap_name: str = "RdYlBu",
    display_legend: bool = True,
    display_axes: bool = True,
) -> plt.Axes:
    """Plot a mesh tags object on the provided (or, if None, the current) axes object.

    Args:
        mesh: the corresponding mesh.
        mesh_tags: the mesh tags.
        ax: (optional) the matplotlib axes.
        display_indices: (optional) boolean, if True displays the indices of the cells/facets.
        expression_levelset: (optional), if not None, display the contour line of the levelset.

    Returns:
        A matplotlib axis with the corresponding plot.
    """
    if ax is None:
        ax = plt.gca()  # type: ignore

    if not display_axes:
        ax.set_axis_off()
    ax.set_aspect("equal")
    points = mesh.geometry.x

    # Get unique tags and create a custom colormap
    cmap = cm.get_cmap(cmap_name)
    norm = mcolors.Normalize(vmin=vbounds[0], vmax=vbounds[1])

    cells_map = mesh.topology.index_map(mesh.topology.dim)
    num_cells = cells_map.size_global

    mappable: mpl_collections.Collection
    cells = mesh.geometry.dofmap
    tria = tri.Triangulation(points[:, 0], points[:, 1], cells)
    cell_colors = np.zeros((cells.shape[0],))

    for c in range(num_cells):
        cell_colors[c] = function.x.array[c]
    mappable = ax.tripcolor(tria, cell_colors, edgecolor="k", cmap=cmap, norm=norm)
    divider = make_axes_locatable(ax)
    if display_legend:
        cax = divider.append_axes("right", size="5%", pad=0.05)
        colorbar = plt.colorbar(mappable, cax=cax, norm=norm)
        legend_label = ""
        if label is not None:
            legend_label = label
        colorbar.set_label(legend_label)

    if expression_levelset is not None:
        x_min, x_max = np.min(points[:, 0]), np.max(points[:, 0])
        y_min, y_max = np.min(points[:, 1]), np.max(points[:, 1])
        nx = 1000
        ny = 1000
        xs = np.linspace(x_min, x_max, nx)
        ys = np.linspace(y_min, y_max, ny)

        xx, yy = np.meshgrid(xs, ys)
        xx_rs = xx.reshape(xx.shape[0] * xx.shape[1])
        yy_rs = yy.reshape(yy.shape[0] * yy.shape[1])
        points = np.vstack([xx_rs, yy_rs])
        zz_rs = expression_levelset(points)
        zz = zz_rs.reshape(xx.shape)

        ax.contour(xx, yy, zz, [0.0], linewidths=1.0, colors="w")
    return ax
