import json as jsonlib
import os

import click

from . import __version__
from .commands import convert_to_flashpack
from .deserialization import get_flashpack_file_metadata
from .integrations import patch_integrations

patch_integrations()


def green(text: str) -> str:
    return click.style(text, fg="green")


def red(text: str) -> str:
    return click.style(text, fg="red")


def yellow(text: str) -> str:
    return click.style(text, fg="yellow")


def blue(text: str) -> str:
    return click.style(text, fg="blue")


def magenta(text: str) -> str:
    return click.style(text, fg="magenta")


@click.group(name="flashpack")
@click.version_option(__version__)
def main() -> None:
    pass


@main.command(name="metadata")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--show-index", "-i", is_flag=True, help="Show the index of the flashpack file."
)
@click.option("--json", "-j", is_flag=True, help="Output the metadata in JSON format.")
def metadata(path: str, show_index: bool, json: bool) -> None:
    """
    Print the metadata of a flashpack file.
    """
    metadata = get_flashpack_file_metadata(path)
    if not show_index:
        metadata.pop("index")

    if json:
        print(jsonlib.dumps(metadata, indent=2))
    else:
        for k, v in metadata.items():
            if k == "index":
                continue
            print(f"{green(k)}: {v}")
        if "index" in metadata and show_index:
            print(f"{green('index')}:")
            num_index_digits = len(str(len(metadata["index"])))
            for i, r in enumerate(metadata["index"]):
                offset_end = r["offset"] + r["length"]
                num_digits = len(str(metadata["total_elems"]))
                element_range = (
                    f"{r['offset']:0{num_digits}d}:{offset_end:0{num_digits}d}"
                )
                element_index = f"{i:0{num_index_digits}d}"
                print(
                    f"  {magenta(element_index)}: {element_range} {blue(r['name'])} {r['shape']}"
                )


@main.command(name="convert")
@click.argument("path_or_repo_id", type=str)
@click.argument("destination_path", type=click.Path(), required=False)
@click.option(
    "--subfolder",
    type=str,
    help="The subfolder of the model. Only used when path_or_repo_id is a repo_id.",
)
@click.option(
    "--variant",
    type=str,
    help="The variant of the model. Only used when path_or_repo_id is a repo_id.",
)
@click.option("--dtype", type=str, help="The dtype of the flashpack file.")
@click.option(
    "--ignore-names",
    type=str,
    help="The names of the tensors to ignore.",
    multiple=True,
)
@click.option(
    "--ignore-prefixes",
    type=str,
    help="The prefixes of the tensors to ignore.",
    multiple=True,
)
@click.option(
    "--ignore-suffixes",
    type=str,
    help="The suffixes of the tensors to ignore.",
    multiple=True,
)
@click.option(
    "--use-transformers", is_flag=True, help="Use transformers to convert the model."
)
@click.option(
    "--use-diffusers", is_flag=True, help="Use diffusers to convert the model."
)
def convert(
    path_or_repo_id: str,
    destination_path: str,
    subfolder: str,
    variant: str,
    dtype: str,
    ignore_names: list[str],
    ignore_prefixes: list[str],
    ignore_suffixes: list[str],
    use_transformers: bool,
    use_diffusers: bool,
) -> None:
    """
    Convert a model to a flashpack file.
    """
    try:
        result_path = convert_to_flashpack(
            path_or_repo_id,
            destination_path,
            dtype=dtype,
            ignore_names=ignore_names,
            ignore_prefixes=ignore_prefixes,
            ignore_suffixes=ignore_suffixes,
            use_transformers=use_transformers,
            use_diffusers=use_diffusers,
            subfolder=subfolder,
            variant=variant,
        )
        print(green(f"Success: Saved to {os.path.abspath(result_path)}"))
    except Exception as e:
        print(red(f"Error: {e}"))
        exit(1)


if __name__ == "__main__":
    main()
