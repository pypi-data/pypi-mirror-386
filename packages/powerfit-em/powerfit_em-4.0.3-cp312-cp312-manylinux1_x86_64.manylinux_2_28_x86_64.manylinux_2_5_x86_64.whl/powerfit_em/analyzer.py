from numpy import bool, greater_equal, log, zeros
from scipy.ndimage import label, maximum_position


class Analyzer:
    def __init__(
        self,
        corr,
        rotmat,
        rotmat_ind,
        steps=5,
        voxelspacing: float = 1.0,
        origin=(0, 0, 0),
        z_sigma: float = 1.0,
    ):
        self._corr = corr
        self._rotmat = rotmat
        self._rotmat_ind = rotmat_ind
        self._voxelspacing = voxelspacing
        self._origin = origin
        self._z_sigma = z_sigma
        self.steps = steps
        self._solutions = None

    @property
    def corr(self):
        return self._corr

    @property
    def rot(self):
        return self._rot

    @property
    def steps(self):
        return self._steps

    @steps.setter
    def steps(self, steps):
        self._steps = steps
        self._watershed()
        self._solutions = None

    @property
    def voxelspacing(self):
        return self._voxelspacing

    @voxelspacing.setter
    def voxelspacing(self, voxelspacing):
        self._solutions = None
        self._voxelspacing = voxelspacing

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, origin):
        self._solutions = None
        self._origin = origin

    @property
    def solutions(self) -> list[list[float]]:
        if self._solutions is None:
            self._generate_solutions()
        return self._solutions

    def _generate_solutions(self):
        solutions: list[list[float]] = []
        for pos in self._positions:
            solution: list[float] = []
            # To support scipy 0.14.0 cast pos into tuple of ints since
            # maximum_position returns a list of tuples of floats
            pos = tuple(int(p) for p in pos)
            lcc = self._corr[pos]
            solution.append(lcc)
            fishers_z = 0.5 * (log(1 + lcc) - log(1 - lcc))
            solution.append(fishers_z)
            rel_z = fishers_z / self._z_sigma
            solution.append(rel_z)
            z, y, x = [coor * self._voxelspacing + shift for coor, shift in zip(pos, self._origin[::-1], strict=False)]
            rotmat = self._rotmat[int(self._rotmat_ind[pos])]
            solution += [x, y, z] + list(rotmat.ravel())
            solutions.append(solution)
        self._solutions = sorted(solutions, key=lambda cc: cc[0], reverse=True)

    def _watershed(self):
        """Get positions of high correlation values using watershed
        algorithm
        """
        max_cc = self._corr.max()
        min_cc = 0.5 * max_cc
        stepsize = (max_cc - min_cc) / self._steps
        cutoff = max_cc
        positions = []
        mask = zeros(self._corr.shape, dtype=bool)
        for _ in range(self._steps):
            cutoff -= stepsize
            greater_equal(self._corr, cutoff, mask)
            labels, nfeatures = label(mask)
            positions += maximum_position(self._corr, labels, list(range(1, nfeatures + 1)))
        self._positions = set(positions)

    def tofile(self, out="solutions.out", delimiter=None):
        """Write solutions to file.

        Arguments:
            out: str, output file name (default: 'solutions.out')
            delimiter: str, delimiter for the output file. Defaults to fixed width output.
                Can be ',' or '\t'. With delimiter set the header will not have leading '#'.
        """

        if self._solutions is None:
            self._generate_solutions()

        write_file(self._solutions, out, delimiter)


def write_file(solutions: list[list[str | float]], out: str, delimiter: str | None):
    fit_many = len(solutions[0]) == 16
    headers = [
        "#rank",
        "cc",
        "Fish-z",
        "rel-z",
        "x",
        "y",
        "z",
        "a11",
        "a12",
        "a13",
        "a21",
        "a22",
        "a23",
        "a31",
        "a32",
        "a33",
    ]

    max_name_length = 0
    if fit_many:
        headers.insert(1, "pdb-filename")
        max_name_length = max([len(x[0]) for x in solutions])

    with open(out, "w") as f:
        if delimiter is None:
            header_fmt = ["{:<6s}"] + ["{:>6s}"] * 3 + ["{:>8s}"] * 3 + ["{:>6s}"] * 9
            if fit_many:
                header_fmt.insert(1, "{:<" + str(max_name_length) + "s}")
            line = " ".join(header_fmt) + "\n"
            f.write(line.format(*headers))

            line_fmt = ["{:<6d}"] + ["{:6.3f}"] * 3 + ["{:8.3f}"] * 3 + ["{:6.3f}"] * 9
            if fit_many:
                line_fmt.insert(1, "{:<" + str(max_name_length) + "s}")
            line = " ".join(line_fmt) + "\n"
            for n, sol in enumerate(solutions):
                f.write(line.format(n + 1, *sol))
        else:
            # Write header
            headers[0] = headers[0].lstrip("#")
            f.write(delimiter.join(headers) + "\n")
            for n, sol in enumerate(solutions):
                row = [n + 1] + sol
                # Format all values as floats with 3 decimals except rank (int)
                row_str = (
                    [str(row[0])]
                    + [f"{v:.3f}" for v in row[1:4]]
                    + [f"{v:.3f}" for v in row[4:7]]
                    + [f"{v:.3f}" for v in row[7:]]
                )
                if fit_many:
                    row_str.insert(1, str(row[1]))
                f.write(delimiter.join(row_str) + "\n")
