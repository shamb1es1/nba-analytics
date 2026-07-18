from __future__ import annotations

import importlib
import inspect
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nba_api.stats.endpoints._base import Endpoint
from requests.exceptions import RequestException


def get_endpoint_class(module_name: str) -> type[Endpoint]:
    """Find the endpoint class inside an nba_api endpoint module."""

    module = importlib.import_module(
        f"nba_api.stats.endpoints.{module_name}"
    )

    endpoint_classes = [
        obj for _, obj in inspect.getmembers(module, inspect.isclass)
        if (
            issubclass(obj, Endpoint)
            and obj is not Endpoint
            and obj.__module__ == module.__name__
        )
    ]

    if len(endpoint_classes) != 1:
        raise RuntimeError(
            f"Expected one endpoint class in {module_name}; "
            f"found {len(endpoint_classes)}."
        )

    return endpoint_classes[0]


def describe_endpoint(module_name: str) -> None:
    """Print required parameters, defaults, and expected datasets."""

    endpoint_class = get_endpoint_class(module_name)
    signature = inspect.signature(endpoint_class)

    print(f"\nEndpoint class: {endpoint_class.__name__}")
    print(f"URL endpoint: {endpoint_class.endpoint}\n")

    for name, parameter in signature.parameters.items():
        if name == "self":
            continue

        required = parameter.default is inspect.Parameter.empty
        default = None if required else parameter.default

        print(
            f"{name:<40} "
            f"required={required:<5} "
            f"default={default!r}"
        )

    print("\nExpected datasets:")
    for dataset in endpoint_class.expected_data:
        print(f"- {dataset}")


def validate_parameters(
    endpoint_class: type[Endpoint],
    parameters: dict[str, Any],
) -> None:
    signature = inspect.signature(endpoint_class)
    valid_parameters = set(signature.parameters)

    unknown = set(parameters) - valid_parameters

    if unknown:
        raise ValueError(
            f"Unknown parameters for {endpoint_class.__name__}: "
            f"{sorted(unknown)}"
        )

    missing = [
        name
        for name, parameter in signature.parameters.items()
        if (
            name != "self"
            and parameter.default is inspect.Parameter.empty
            and name not in parameters
        )
    ]

    if missing:
        raise ValueError(f"Missing required parameters: {missing}")


def run_endpoint(
    module_name: str,
    parameters: dict[str, Any],
    output_directory: str | Path,
    timeout: int = 60,
    retries: int = 3,
    retry_delay: float = 3,
) -> dict[str, Path]:
    endpoint_class = get_endpoint_class(module_name)
    validate_parameters(endpoint_class, parameters)

    signature = inspect.signature(endpoint_class)
    request_parameters = parameters.copy()

    if "timeout" in signature.parameters:
        request_parameters["timeout"] = timeout

    deferred_request = "get_request" in signature.parameters

    if deferred_request:
        request_parameters["get_request"] = False
        response = endpoint_class(**request_parameters)

    for attempt in range(1, retries + 1):
        try:
            if deferred_request:
                response.get_request()
            else:
                response = endpoint_class(**request_parameters)

            break

        except RequestException:
            if attempt == retries:
                raise

            time.sleep(retry_delay * attempt)

    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    saved_files: dict[str, Path] = {}

    raw_path = output_directory / "raw_response.json"

    with raw_path.open("w", encoding="utf-8") as file:
        json.dump(response.get_dict(), file, indent=2)

    saved_files["raw_response"] = raw_path

    dataset_names = list(response.get_available_data())
    data_frames = response.get_data_frames()

    for index, data_frame in enumerate(data_frames):
        dataset_name = (
            dataset_names[index]
            if index < len(dataset_names)
            else f"dataset_{index + 1}"
        )

        filename = re.sub(
            r"(?<!^)(?=[A-Z])",
            "_",
            dataset_name,
        ).lower()

        csv_path = output_directory / f"{filename}.csv"
        data_frame.to_csv(csv_path, index=False)

        saved_files[dataset_name] = csv_path

    metadata = {
        "endpoint_module": module_name,
        "endpoint_class": endpoint_class.__name__,
        "parameters": parameters,
        "request_url": response.get_request_url(),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "datasets": dataset_names,
    }

    metadata_path = output_directory / "metadata.json"

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, default=str)

    saved_files["metadata"] = metadata_path

    return saved_files