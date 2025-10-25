import dask.array as da
import matplotlib.pyplot as plt
import numpy as np


class Array2D:
    """
    Surcouche Numpy pour représenter la sélection d'une zone dans un array 2D.

    arr = np.arange(81).reshape(9, 9)
    a2d = Array2D(arr)
    a2d[indexes]
    """

    def __init__(self, array2d):
        assert array2d.ndim == 2, "L'array doit être 2D"
        self.array = array2d
        self.dims = array2d.shape

    def __getitem__(self, key):
        selection = np.zeros(self.dims, dtype=bool)
        selection[key] = True

        fig, ax = plt.subplots()
        ax.imshow(np.ones(self.dims), cmap="Greys", alpha=0.1)  # fond gris clair
        ax.imshow(selection, cmap="Blues", alpha=0.6)

        # Ajout de la grille (lignes fines entre les cases)
        ax.set_xticks(np.arange(-0.5, self.dims[1], 1), minor=True)
        ax.set_yticks(np.arange(-0.5, self.dims[0], 1), minor=True)
        ax.grid(which="minor", color="black", linestyle="-", linewidth=0.5)

        # Afficher les ticks principaux avec les indices
        ax.set_xticks(np.arange(self.dims[1]))
        ax.set_yticks(np.arange(self.dims[0]))
        ax.set_xticklabels(np.arange(self.dims[1]))
        ax.set_yticklabels(np.arange(self.dims[0]))

        # ax.invert_yaxis()
        ax.xaxis.set_ticks_position("top")
        ax.xaxis.set_label_position("top")
        plt.show()

    def __repr__(self):
        return self.array.__repr__()


class DaskArray2D:
    """
    arr = da.arange(81).reshape(9, 9).rechunk((3, 3))
    da2d = DaskArray2D(arr)
    da2d[indexes]
    """

    def __init__(self, dask_array):
        if not isinstance(dask_array, da.Array):
            raise TypeError("L'argument doit être un dask.array.Array")
        if dask_array.ndim != 2:
            raise ValueError("DaskArray2D ne supporte que les arrays 2D")

        self.arr = dask_array
        self.dims = dask_array.shape
        self.chunk_sizes = dask_array.chunks  # tuple de tuples (par dimension)

    def __getitem__(self, key):
        selection = np.zeros(self.dims, dtype=bool)
        selection[key] = True

        fig, ax = plt.subplots()
        ax.imshow(np.ones(self.dims), cmap="Greys", alpha=0.1)
        ax.imshow(selection, cmap="Blues", alpha=0.6)

        # Ticks majeurs centrés sur les pixels (indices)
        ax.set_xticks(np.arange(self.dims[1]), minor=False)
        ax.set_yticks(np.arange(self.dims[0]), minor=False)

        # Labels pour ticks
        ax.set_xticklabels(np.arange(self.dims[1]))
        ax.set_yticklabels(np.arange(self.dims[0]))

        # Grille mineure entre pixels
        ax.set_xticks(np.arange(-0.5, self.dims[1], 1), minor=True)
        ax.set_yticks(np.arange(-0.5, self.dims[0], 1), minor=True)
        ax.grid(which="minor", color="black", linestyle="-", linewidth=0.5)

        # Fonction utilitaire pour positions cumulées des chunks
        def cumsum_chunks(chunks):
            positions = [0]
            for size in chunks:
                positions.append(positions[-1] + size)
            return positions

        # Positions lignes chunks (à -0.5 pour coller à la grille)
        x_chunk_lines = cumsum_chunks(self.chunk_sizes[1])
        y_chunk_lines = cumsum_chunks(self.chunk_sizes[0])
        x_chunk_lines_shifted = [x - 0.5 for x in x_chunk_lines]
        y_chunk_lines_shifted = [y - 0.5 for y in y_chunk_lines]

        # Tracer lignes de séparation des chunks avec axvline et axhline
        for x in x_chunk_lines_shifted:
            ax.axvline(x=x, color="red", linewidth=2)
        for y in y_chunk_lines_shifted:
            ax.axhline(y=y, color="red", linewidth=2)

        # ax.invert_yaxis()
        ax.xaxis.set_ticks_position("top")
        ax.xaxis.set_label_position("top")
        plt.show()
