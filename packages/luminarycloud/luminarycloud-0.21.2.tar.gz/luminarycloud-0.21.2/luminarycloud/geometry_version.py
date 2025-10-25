# Copyright 2023-2024 Luminary Cloud, Inc. All Rights Reserved.
from datetime import datetime

from ._client import get_default_client
from ._helpers._timestamp_to_datetime import timestamp_to_datetime
from ._helpers.pagination import PaginationIterator
from ._proto.api.v0.luminarycloud.geometry import geometry_pb2 as geometrypb
from ._proto.geometry import geometry_pb2 as gpb
from ._wrapper import ProtoWrapper, ProtoWrapperBase
from .geometry import Geometry, get_geometry
from .params.geometry import Surface, Volume
from .tag import Tag
from .types import Vector3


@ProtoWrapper(geometrypb.GeometryVersion)
class GeometryVersion(ProtoWrapperBase):
    """Represents a GeometryVersion object."""

    id: str
    "Geometry Version ID."
    geometry_id: str
    "Geometry ID."

    _proto: geometrypb.GeometryVersion

    @property
    def create_time(self) -> datetime:
        """
        The time the geometry was created.
        """
        return timestamp_to_datetime(self._proto.create_time)

    def geometry(self) -> Geometry:
        """
        Get the parent geometry.
        """
        return get_geometry(self._proto.geometry_id)

    def list_tags(self) -> list[Tag]:
        """
        Get the tags associated with this geometry version.

        Returns
        -------
        list[Tag]
        """
        req = geometrypb.ListTagsRequest(
            geometry_version_id=self.id,
        )
        res: geometrypb.ListTagsResponse = get_default_client().ListTags(req)
        return [Tag(t) for t in res.tags]

    def list_entities(self) -> tuple[list[Surface], list[Volume]]:
        """
        List all the entities in this geometry version.

        Returns
        -------
        surfaces : list[Surface]
            A list of all the surfaces in this geometry version.
        volumes : list[Volume]
            A list of all the volumes in this geometry version.
        """

        res: geometrypb.ListGeometryEntitiesResponse = get_default_client().ListGeometryEntities(
            geometrypb.ListGeometryEntitiesRequest(geometry_version_id=self.id)
        )
        surfaces = [
            Surface(
                geometry_id=self.id,
                id=f.id,
                _native_id=f.native_id,
                bbox_min=Vector3(f.bbox_min.x, f.bbox_min.y, f.bbox_min.z),
                bbox_max=Vector3(f.bbox_max.x, f.bbox_max.y, f.bbox_max.z),
            )
            for f in res.faces
        ]
        volumes = [
            Volume(
                geometry_id=self.id,
                id=str(b.id),
                _lcn_id=str(b.lcn_id),
                bbox_min=Vector3(b.bbox_min.x, b.bbox_min.y, b.bbox_min.z),
                bbox_max=Vector3(b.bbox_max.x, b.bbox_max.y, b.bbox_max.z),
            )
            for b in res.bodies
        ]
        return surfaces, volumes

    def copy_to_new_geometry(self, name: str = "", request_id: str = "") -> Geometry:
        """
        Copy this GeometryVersion and create a new Geometry containing only that newly copied version.

        Parameters
        ----------
        name : str, optional
            The name of the new Geometry. If not provided, a default name will be used.
        request_id : str, optional
            A deduplication key, useful for idempotency. The first time copy_to_new_geometry() is
            called with a given request_id, a new geometry will be created. Subsequent calls with
            the same request_id will return the same geometry. If not provided, no deduplication is
            done. Max length: 256 characters.

        Returns
        -------
        Geometry
            The new Geometry containing only the newly copied GeometryVersion.
        """
        req = geometrypb.CopyGeometryFromVersionRequest(
            geometry_version_id=self.id,
            name=name,
            request_id=request_id,
        )
        res: geometrypb.CopyGeometryFromVersionResponse = (
            get_default_client().CopyGeometryFromVersion(req)
        )
        return Geometry(res.geometry)

    def _list_features(
        self,
    ) -> list[gpb.Feature]:
        """
        List the features in this geometry version.

        Returns
        -------
        features : list[Feature]
            A list of the features in this geometry version.
        """
        req = geometrypb.ListGeometryFeaturesRequest(
            geometry_version_id=self.id,
        )
        res: geometrypb.ListGeometryFeaturesResponse = get_default_client().ListGeometryFeatures(
            req
        )
        return list(res.features)

    def _list_feature_issues(
        self,
    ) -> list[gpb.FeatureIssues]:
        """
        List any issues with features in this geometry version.

        Returns
        -------
        feature_issues : list[FeatureIssues]
            A list of any issues with features in this geometry version. Issues may be
            informational, warnings or errors.
        """
        req = geometrypb.ListGeometryFeatureIssuesRequest(
            geometry_version_id=self.id,
        )
        res: geometrypb.ListGeometryFeatureIssuesResponse = (
            get_default_client().ListGeometryFeatureIssues(req)
        )
        return list(res.features_issues)

    def to_code(self) -> str:
        """
        Returns the Python code that creates (from scratch) an identical geometry of
        this particular version.

        Returns
        -------
        str
            The SDK code that can be used to recreate this specific geometry version.

        Examples
        --------
        >>> geometry_version = lc.get_geometry_version("version-id")
        >>> python_code = geometry_version.to_code()
        >>> print(python_code)
        """
        req = geometrypb.GetSdkCodeRequest(
            geometry_id=self.geometry_id,
            geometry_version_id=self.id,
        )
        res: geometrypb.GetSdkCodeResponse = get_default_client().GetSdkCode(req)
        return res.sdk_code


class GeometryVersionIterator(PaginationIterator[GeometryVersion]):
    """Iterator class for geometry versions that provides length hint."""

    def __init__(self, geometry_id: str, unfiltered: bool, page_size: int):
        super().__init__(page_size)
        self._geometry_id: str = geometry_id
        self._unfiltered: bool = unfiltered

    def _fetch_page(
        self, page_size: int, page_token: str
    ) -> tuple[list[GeometryVersion], str, int]:
        req = geometrypb.ListGeometryVersionsRequest(
            page_size=page_size,
            page_token=page_token,
            geometry_id=self._geometry_id,
            unfiltered=self._unfiltered,
        )
        res = self._client.ListGeometryVersions(req)
        return (
            [GeometryVersion(gv) for gv in res.geometry_versions],
            res.next_page_token,
            res.total_count,
        )


def get_geometry_version(id: str) -> GeometryVersion:
    """
    Get a geometry version by its ID.

    Parameters
    ----------
    id : str
        ID of the geometry version to get.

    Returns
    -------
    GeometryVersion
        The requested GeometryVersion.
    """

    req = geometrypb.GetGeometryVersionRequest(geometry_version_id=id)
    res: geometrypb.GetGeometryVersionResponse = get_default_client().GetGeometryVersion(req)
    return GeometryVersion(res.geometry_version)


def update_geometry_version(id: str, name: str) -> GeometryVersion:
    """
    Update a geometry version.

    Parameters
    ----------
    id : str
        ID of the geometry version to update.
    name : str
        The new name for the geometry version. Pass an empty string to clear the name.

    Returns
    -------
    GeometryVersion
        The updated GeometryVersion.
    """

    req = geometrypb.UpdateGeometryVersionRequest(geometry_version_id=id, name=name)
    res: geometrypb.UpdateGeometryVersionResponse = get_default_client().UpdateGeometryVersion(req)
    return GeometryVersion(res.geometry_version)
