import numpy as np

from .geometry import GeometryData


class GeomFluxloops(GeometryData):
    """
    Manipulation class for fluxloops.

    - plot: plot flux loop positions in 2D R-Z and 3D

    """

    def _get_all_coords(self, data, r_z_coord):
        """
        Recursively loop over tree, and retrieve pickup coil co-ordinates.
        :param data: data tree (instance of StructuredWritable, with pickup coil tree structure)
        :param r_z_coord: R,Z coordinates will be appended to this list
        :return:
        """
        child_names = [child.name for child in data.children]

        if "coordinate" in child_names and "geometry" in child_names:
            r_z_coord.append(data["coordinate"].r)
            r_z_coord.append(data["coordinate"].z)
        else:
            for child in data.children:
                self._get_all_coords(child, r_z_coord)

    def plot(self, ax_2d=None, ax_3d=None, show=True, color=None):
        """
        Plot the fluxloop positions
        :param data: data tree (instance of StructuredWritable, with pickup coil tree structure)
        :param ax_2d: Axis on which to plot location of pickup coils in R-Z (2D) plane.
                      If None, then an axis will be created.
        """
        import matplotlib.pyplot as plt

        data = self.data

        # Get co-ordiantes
        r_z_to_plot = []

        self._get_all_coords(data, r_z_to_plot)

        if len(r_z_to_plot) == 0:
            return

        # Create axes if necessary
        # Create axes if necessary
        if ax_2d is None:
            fig = plt.figure()
            if ax_2d is None:
                ax_2d = fig.add_subplot(121)
                #ax_2d_xy = fig.add_subplot(122)

        # Plot
        if ax_2d is not None:
            R_coords = r_z_to_plot[::2]
            Z_coords = r_z_to_plot[1::2]

            # plot
            ax_2d.plot(R_coords, Z_coords, c=color, markersize=4, linewidth=0, marker="o", markeredgecolor=color)
            ax_2d.set_xlabel('R [m]')
            ax_2d.set_ylabel('Z [m]')

        if ax_3d is not None:
            # Assuming loops are centred around R = 0
            n_loops = len(r_z_to_plot) // 2
            for iloop in range(0,n_loops):
                loop_radius = r_z_to_plot[iloop*2]
                loop_centre_z = r_z_to_plot[iloop * 2 + 1]

                theta = np.linspace(-1 * np.pi, np.pi, 100)
                z_coord = [loop_centre_z]*100
                x_coord = loop_radius * np.sin(theta)
                y_coord = loop_radius * np.cos(theta)

                ax_3d.plot(x_coord, y_coord, z_coord)

        if show:
            plt.show()


