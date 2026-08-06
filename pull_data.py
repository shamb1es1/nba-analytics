import argparse
import ast
import json
from pathlib import Path

from endpoint_runner import (
    describe_endpoint,
    get_endpoint_class,
    run_endpoint,
)


def ask_to_include_headshot_urls() -> bool:
    """Ask whether exported player datasets should include headshot URLs."""

    while True:
        answer = input(
            "\nInclude player headshot URLs? [y/N]: "
        ).strip().lower()

        if answer in {"", "n", "no"}:
            return False

        if answer in {"y", "yes"}:
            return True

        print("Please enter y or n.")


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
        SyntaxError,
        ValueError,
        OSError,
    ) as error:
        print(f"\nCould not read parameters: {error}")
        return

    if not isinstance(parameters, dict):
        print("\nParameters must be provided as a dictionary.")
        return

    include_headshot_urls = ask_to_include_headshot_urls()

    parameters_str = "".join(f"[{value}]" for value in parameters.values())

    file_name = f"{endpoint_name}{parameters_str}"

    try:
        saved_files = run_endpoint(
            module_name=endpoint_name,
            parameters=parameters,
            output_directory=Path("data/raw") / file_name,
            include_headshot_urls=include_headshot_urls,
        )
    except Exception as error:
        print(f"\nRequest failed: {error}")
        return

    print("\nFiles saved:")

    for dataset_name, path in saved_files.items():
        print(f"- {dataset_name}: {path}")


if __name__ == "__main__":
    main()
