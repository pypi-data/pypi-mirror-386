from __future__ import annotations

from abc import abstractmethod
from typing import Union, TYPE_CHECKING

from .CRS import CRS, WGS84

if TYPE_CHECKING:
    from .bbox import BBox
    from .point import Point


class SpatialGeometry:
    """
    An abstract base class for representing spatial geometries.

    This class provides a common interface for working with different types of
    spatial geometries, such as points, lines, and polygons. It defines a set of
    abstract methods that must be implemented by concrete subclasses, as well as
    a number of common properties and methods.

    Attributes:
        _crs (CRS): The coordinate reference system (CRS) of the geometry.

    Args:
        *args: Positional arguments passed to the subclass's constructor.
        crs (Union[CRS, str], optional): The coordinate reference system (CRS)
            of the geometry. Defaults to WGS84.
        **kwargs: Keyword arguments passed to the subclass's constructor.
    """

    def __init__(self, *args, crs: Union[CRS, str] = WGS84, **kwargs):
        """
        Initializes a new SpatialGeometry object.
        """

        if not isinstance(crs, CRS):
            crs = CRS(crs)

        self._crs = crs

    @property
    def crs(self) -> CRS:
        """
        Gets the coordinate reference system (CRS) of the geometry.

        Returns:
            CRS: The coordinate reference system (CRS) of the geometry.
        """

        return self._crs

    @property
    @abstractmethod
    def bbox(self) -> "BBox":
        """
        Gets the bounding box of the geometry.

        Returns:
            BBox: The bounding box of the geometry.
        """

        pass

    @abstractmethod
    def to_crs(self, CRS: Union[CRS, "str"]) -> SpatialGeometry:
        """
        Transforms the geometry to a new coordinate reference system (CRS).

        Args:
            CRS (Union[CRS, str]): The new coordinate reference system (CRS).

        Returns:
            SpatialGeometry: The transformed geometry.
        """

        pass

    @property
    def latlon(self) -> SpatialGeometry:
        """
        Transforms the geometry to the WGS84 coordinate reference system (CRS).

        Returns:
            SpatialGeometry: The transformed geometry.
        """

        return self.to_crs(WGS84)

    @property
    @abstractmethod
    def centroid(self) -> "Point":
        """
        Gets the centroid of the geometry.

        Returns:
            Point: The centroid of the geometry.

        Raises:
            NotImplementedError: If the centroid property is not implemented by
                the subclass.
        """

        raise NotImplementedError(f"centroid property not implemented by {self.__class__.__name__}")

    @property
    def centroid_latlon(self) -> "Point":
        """
        Gets the centroid of the geometry in the WGS84 coordinate reference
        system (CRS).

        Returns:
            Point: The centroid of the geometry in the WGS84 coordinate
                reference system (CRS).
        """

        return self.centroid.latlon

    @property
    def local_UTM_proj4(self) -> str:
        from .local_UTM_proj4 import local_UTM_proj4
        centroid = self.centroid.latlon
        return local_UTM_proj4(centroid)
