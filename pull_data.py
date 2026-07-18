import argparse
import ast
import json
from pathlib import Path

from endpoint_runner import (
    describe_endpoint,
    get_endpoint_class,
    run_endpoint,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "endpoint",
        nargs="?",
        help="nba_api endpoint module name",
    )

    parser.add_argument(
        "config",
        nargs="?",
        help="JSON parameters, Python dictionary, or JSON file path",
    )

    args = parser.parse_args()

    endpoint_name = args.endpoint

    if endpoint_name is None:
        endpoint_name = input(
            "Enter endpoint module name: "
        ).strip()

    endpoint_name = endpoint_name.lower()

    try:
        get_endpoint_class(endpoint_name)
    except (ModuleNotFoundError, RuntimeError) as error:
        print(f"\nEndpoint not found: {error}")
        return

    print("\nEndpoint found.")
    describe_endpoint(endpoint_name)

    config_input = args.config

    if config_input is None:
        config_input = input(
            "\nEnter parameters or JSON file path: "
        ).strip()

    config_path = Path(config_input)

    try:
        if config_path.is_file():
            with config_path.open(encoding="utf-8") as file:
                parameters = json.load(file)
        else:
            try:
                # Standard JSON:
                # {"season": "2025-26"}
                parameters = json.loads(config_input)

            except json.JSONDecodeError:
                # Python dictionary syntax:
                # {'season': '2025-26'}
                parameters = ast.literal_eval(config_input)

    except (
        json.JSONDecodeError,
        SyntaxError,
        ValueError,
        OSError,
    ) as error:
        print(f"\nCould not read parameters: {error}")
        return

    if not isinstance(parameters, dict):
        print("\nParameters must be provided as a dictionary.")
        return

    try:
        saved_files = run_endpoint(
            module_name=endpoint_name,
            parameters=parameters,
            output_directory=Path("data/raw") / endpoint_name,
        )
    except Exception as error:
        print(f"\nRequest failed: {error}")
        return

    print("\nFiles saved:")

    for dataset_name, path in saved_files.items():
        print(f"- {dataset_name}: {path}")


if __name__ == "__main__":
    main()