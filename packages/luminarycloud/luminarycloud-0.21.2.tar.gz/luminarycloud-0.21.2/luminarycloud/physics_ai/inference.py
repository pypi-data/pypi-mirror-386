# File: python/sdk/luminarycloud/inference/inference.py
# Copyright 2025 Luminary Cloud, Inc. All Rights Reserved.
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from json import loads as json_loads, dumps as json_dumps
from dataclasses import dataclass
import base64
import os
import urllib.request

from .._client import get_default_client
from .._helpers._timestamp_to_datetime import timestamp_to_datetime
from .._proto.api.v0.luminarycloud.inference import inference_pb2 as inferencepb
from .._proto.inferenceservice import inferenceservice_pb2 as inferenceservicepb
from .._wrapper import ProtoWrapper, ProtoWrapperBase
from ..project import Project
from ..project import Project
from .._helpers import upload_file
from .._proto.upload import upload_pb2 as uploadpb
from ..types.ids import PhysicsAiModelVersionID


@dataclass
class ExtAeroInferenceResult:
    """Result of an external aerodynamic inference job.

    Attributes
    ----------
    drag_force: float
        The drag force returned from the inference.
    lift_force: float
        The lift force returned from the inference.
    wall_shear_stress:
        A dict containing wall shear stress data, or None if not available.
    pressure_surface:
        A dict containing pressure surface stress data, or None if not available.
    """

    drag_force: float
    lift_force: float
    wall_shear_stress: dict[str, Any] | None
    pressure_surface: dict[str, Any] | None

    def __init__(self, inference_result: dict[str, Any]) -> None:
        self.drag_force = inference_result["drag_force"]
        self.lift_force = inference_result["lift_force"]
        self.wall_shear_stress = inference_result.get("wall-shear-stress", None)
        self.pressure_surface = inference_result.get("pressure_surface", None)


def external_aero_inference(
    project: Project,
    stl_file: str,
    model_version_id: PhysicsAiModelVersionID,
    conditions: Optional[Dict[str, Any]] = None,
    settings: Optional[Dict[str, Any]] = None,
    write_visualization_data=False,
) -> ExtAeroInferenceResult:
    """Performs an inference job returning external aerodynamic results.
    Parameters
    ----------
    project : Project
        The project to which the inference files will be added.
    stl_file : str
        Fullpath the STL file to be used for inference.
    model_version_id : PhysicsAiModelVersionID
        The ID of the trained model version to use for inference.
    conditions : Dict[str, Any], optional
        Dictionary of conditions to be passed to the inference service (e.g., alpha, beta, etc.).
    settings : Dict[str, Any], optional
        Dictionary of settings to be passed to inference service (e.g., stencil_size)
    write_visualization_data : bool, optional
        Whether to write LC visualization data for visualization by Luminary.


    Returns
    ExtAeroInferenceResult
        Result of the external aerodynamic inference job.

    warning:: This feature is experimental and may change or be removed without notice.
    """

    result = perform_inference(
        project, stl_file, model_version_id, conditions, settings, write_visualization_data
    )
    return ExtAeroInferenceResult(result)


def perform_inference(
    project: Project,
    stl_file: str,
    model_version_id: PhysicsAiModelVersionID,
    conditions: Optional[Dict[str, Any]] = None,
    settings: Optional[Dict[str, Any]] = None,
    write_visualization_data=False,
) -> dict[str, Any]:
    """Creates an inference service job.
    Parameters
    ----------
    project : Project
        The project to which the inference files will be added.
    stl_file : str
        Fullpath the STL file to be used for inference.
    model_version_id : PhysicsAiModelVersionID
        The ID of the trained model version to use for inference.
    conditions : Dict[str, Any], optional
        Dictionary of conditions to be passed to the inference service (e.g., alpha, beta, etc.).
    settings : Dict[str, Any], optional
        Dictionary of settings to be passed to inference service (e.g., stencil_size)
    write_visualization_data : bool, optional
        Whether to write LC visualization data for visualization by Luminary.


    Returns
    dict[str, Any]
        Response from the server as key-value pairs.

    warning:: This feature is experimental and may change or be removed without notice.
    """

    client = get_default_client()

    def upload_if_file(fname: str) -> str:
        if os.path.exists(fname) and os.path.isfile(fname):
            params = uploadpb.ResourceParams()
            result = upload_file(client, project.id, params, fname)
            return result[1].url
        if fname.startswith("gs://"):
            return fname
        raise RuntimeError("Unsupported file for inference")

    def future_file(url: str) -> Callable[[], dict[str, Any]]:
        def download_file() -> dict[str, Any]:
            with urllib.request.urlopen(url) as f:
                serialized = f.read()
                jsondata = json_loads(serialized)
                data = base64.b64decode(jsondata["data"])
                jsondata["data"] = data
                return jsondata

        return download_file

    stl_url = upload_if_file(stl_file)

    raw = start_inference_job(
        project, stl_url, model_version_id, conditions, settings, write_visualization_data
    )
    currated: dict[str, Any] = {}
    for k, v in raw.items():
        if isinstance(v, str) and v.startswith("https://"):
            tmp = future_file(v)
            if k.endswith("_url"):
                currated[k[:-4]] = tmp
                currated[k] = v
            else:
                currated[k] = tmp
                currated[k + "_url"] = v
        else:
            currated[k] = v
    return currated


def start_inference_job(
    project: Project,
    stl_url: str,
    model_version_id: PhysicsAiModelVersionID,
    conditions: Optional[Dict[str, Any]] = None,
    settings: Optional[Dict[str, Any]] = None,
    write_visualization_data=False,
) -> dict[str, Any]:
    """Creates an inference service job.
    Parameters
    ----------
    project : Project
        Reference to a project.
    stl_url : str
        URL of the STL file to be used for inference.
    model_version_id : PhysicsAiModelVersionID
        The ID of the trained model version to use for inference.
    conditions : Dict[str, Any], optional
        Dictionary of conditions to be passed to the inference service (e.g., alpha, beta, etc.).
    settings : Dict[str, Any], optional
        Dictionary of settings to be passed to inference service (e.g., stencil_size)
    write_visualization_data : bool, optional
        Whether to write LC visualization data for visualization by Luminary.


    Returns
    dict[str, Any]
        Response from the server as key-value pairs.

    warning:: This feature is experimental and may change or be removed without notice.
    """

    # Embed settings and store as bytes
    settings_bytes = b""
    if settings is not None:
        settings_bytes = json_dumps(settings).encode("utf-8")

    # Convert parameters dict to bytes if provided
    conditions_bytes = b""
    if conditions is not None:
        conditions_bytes = json_dumps(conditions).encode("utf-8")

    req = inferencepb.CreateInferenceServiceJobRequest(
        stl_url=stl_url,
        model_version_id=str(model_version_id),
        conditions=conditions_bytes,
        settings=settings_bytes,
        project_id=project.id,
        write_visualization_data=write_visualization_data,
    )
    res: inferencepb.CreateInferenceServiceJobResponse = (
        get_default_client().CreateInferenceServiceJob(req)
    )

    return json_loads(str(res.response, encoding="utf-8"))
