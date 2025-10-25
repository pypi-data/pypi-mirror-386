from matplotlib import pyplot as plt
import warnings


Point = tuple[float, float]


def cross(point0: Point, point1: Point, point2: Point) -> float:
    """2D cross product (01 x 02): positive if 012 makes a left turn."""
    return (point1[0]-point0[0])*(point2[1]-point0[1]) - (point1[1]-point0[1])*(point2[0]-point0[0])


class Perimeter:

    def __init__(self, name_points: dict[str, Point]) -> None:
        self._name_points: dict[str, Point] = name_points
        self._rejected_names: list[str] = []
        self._convex_hull()

    def _convex_hull(self) -> list[str]:
        """
        Monotone chain convex hull with collinear points included.
        Returns ordered vertices of the hull including collinear boundary points.
        """
        # Sort points by x-coordinate, then by y-coordinate
        sorted_points = sorted(self._name_points.values(), key=lambda p: (p[0], p[1]))

        lower: list[Point] = []
        for point in sorted_points:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
                lower.pop()
            lower.append(point)

        upper: list[Point] = []
        for point in reversed(sorted_points):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
                upper.pop()
            upper.append(point)

        hull: list[Point] = lower[:-1] + upper[:-1]

        # Remove duplicates while preserving order
        seen = set()
        unique_hull = []
        for point in hull:
            if point not in seen:
                unique_hull.append(point)
                seen.add(point)

        # Map points back to names, preserving order
        _reordered_names: list[str] = []
        for point in unique_hull:
            point_name = next((k for k, v in self._name_points.items() if v == point), None)
            if point_name is not None:
                _reordered_names.append(point_name)
        reordered_names: list[str] = list(_reordered_names)
        if len(reordered_names) != len(self._name_points):
            for name in self._name_points:
                if name not in reordered_names:
                    inserted = False
                    for i in range(len(reordered_names)):
                        next_i: int = (i + 1) % len(reordered_names)
                        if cross(self._name_points[reordered_names[i]], self._name_points[reordered_names[next_i]], self._name_points[name]) == 0:
                            reordered_names.insert(i + 1, name)
                            inserted = True
                            break
                    if not inserted:
                        warnings.warn(f"Point {name} not found in hull")
                        self._rejected_names.append(name)

        self.extended_reordered_names: list[str] = reordered_names
        self.extended_reordered_name_points: dict[str, tuple[float, float]] = {name: self._name_points[name] for name in self.extended_reordered_names}

    def coordinates(self, name: str) -> Point:
        return self._name_points[name]

    @property
    def original_points(self) -> dict[str, Point]:
        return self._name_points

    @property
    def original_names(self) -> list[str]:
        return list(self._name_points.keys())

    @property
    def reordered_points(self) -> dict[str, Point]:
        return self.extended_reordered_name_points

    @property
    def reordered_names(self) -> list[str]:
        return self.extended_reordered_names

    @property
    def rejected_names(self) -> list[str]:
        return self._rejected_names

    @property
    def sides(self) -> list[tuple[str, str]]:
        segments: list[tuple[str, str]] = []
        for i in range(len(self.extended_reordered_names)):
            segments.append((self.extended_reordered_names[i], self.extended_reordered_names[(i + 1) % len(self.extended_reordered_names)]))
        return segments

    def plot(self, name_points: dict[str, Point]) -> None:
        # Get points in order
        points = list(name_points.values())
        x_points = [point[0] for point in points]
        y_points = [point[1] for point in points]

        # Close the polygon by adding the first point at the end
        x_points.append(x_points[0])
        y_points.append(y_points[0])

        plt.figure(figsize=(10, 6))
        plt.plot(x_points, y_points, 'b-', linewidth=2, label='Building perimeter')

        # Plot individual points
        plt.plot(x_points[:-1], y_points[:-1], 'ro', markersize=8, label='Vertices')

        # Add point labels
        for name, point in name_points.items():
            plt.annotate(name, point, xytext=(5, 5), textcoords='offset points')

        plt.xlabel('x')
        plt.ylabel('y')
        plt.title('Building perimeter')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.axis('equal')

    def __repr__(self) -> str:
        return ", ".join(self.extended_reordered_names)


if __name__ == "__main__":
    perimeter = Perimeter({'p1': (0, 0), 'p2': (1, 0), 'p3': (0, 2), 'p4': (2, 2), 'p5': (0, 1), 'p6': (0.5, 0), 'p7': (1.5, 1), 'p8': (0, 1.5), 'p9': (0.5, 0.5)})
    print("Original points:", perimeter.original_names)
    print("Reordered points:", perimeter.extended_reordered_names)
    print("Rejected points:", perimeter.rejected_names)
    print("Sides:", perimeter.sides)

    perimeter.plot(perimeter.original_points)
    perimeter.plot(perimeter.reordered_points)
    plt.show()
