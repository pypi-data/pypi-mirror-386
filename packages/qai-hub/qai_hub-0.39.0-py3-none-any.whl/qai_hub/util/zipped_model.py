import os
import zipfile
from typing import Iterable, List, Tuple

SUPPORTED_ZIPPED_MODEL_ASSETS = {
    ".mlmodelc",
    ".mlpackage",
    ".trtmodel",
    ".aimet",
    ".onnx",
}


def zip_model(output_dir_path: str, model_path: str) -> str:
    """
    Zips directory model_path as a base directory.
    Example:
        output_dir_path: "/path/to/out/"
        model_path : "/path/to/model1/model_123.mlmodelc"
        creates following zip file at location "/path/to/out/model_123.zip":
            model_123.zip
                -> model_123.mlmodelc

    Parameters
    ----------
        output_dir_path (str): output directory path to create new archive
        model_path (str): source model path to archive

    Returns
    -------
        zipped_model_path (str): returns zipped file path
    """

    model_path = os.path.abspath(model_path)
    package_name = os.path.basename(model_path)

    # shutil.make_archive is simpler, but uses a compression rate that is
    # prohibitively slow for large models.

    # Reference: Compress levels and times of a single Llama part
    # Level  Size   Time (mm:ss)
    #     0: 7.5 GB          16
    #     1: 3.9 GB        2:05
    #     2: 3.8 GB        2:36
    #     3: 3.6 GB        3:52
    #     6: 3.4 GB       17:48
    compresslevel = 1

    output_path = os.path.join(output_dir_path, package_name + ".zip")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with zipfile.ZipFile(
        output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=compresslevel
    ) as f:
        walk: Iterable[Tuple[str, List[str], List[str]]]
        if os.path.isfile(model_path):
            root_path = os.path.dirname(model_path)
            walk = [(root_path, [], [model_path])]
        else:
            root_path = os.path.join(model_path, "..")
            walk = os.walk(model_path)

        for root, _, files in walk:
            # Create directory entry (can use f.mkdir from Python 3.11)
            rel_root = os.path.relpath(root, root_path)
            if rel_root != ".":
                f.writestr(rel_root + "/", "")
            for file in files:
                f.write(
                    os.path.join(root, file),
                    os.path.relpath(os.path.join(root, file), root_path),
                )
    return output_path


def unzip_model(
    zipped_model_path: str,
    path_to_extract: str,
) -> str:
    """
    Extracts zipped model at provided path
    Example:
        zipped_model_path: "/path/to/input/any_name.mlpackage.zip"
        content of zip file:
            any_name.mlpackage.zip
                -> model.mlpackage
        path_to_extract : "/path/to/out/"
        extracts model.mlpackage.zip at "/path/to/out/model.mlpackage"

    Parameters
    ----------
        zipped_model_path (str): input zipped model to extract
        path_to_extract (str): directory to extract model to

    Returns
    -------
        unzipped_model_path (str): returns unzipped model path

    Raises
    ------
    ValueError
        If only one supported model asset is not present at base path zipped file
    """

    with zipfile.ZipFile(zipped_model_path) as zippedFile:
        model_zip_content = list(
            set(
                [
                    os.path.normpath(name).split(os.sep)[0]
                    for name in zippedFile.namelist()
                ]
            )
        )

        if len(model_zip_content) != 1:
            raise ValueError(
                "Incorrect archived model. "
                f"Expecting only one model asset at base path {SUPPORTED_ZIPPED_MODEL_ASSETS}."
            )

        model_asset_path = list(model_zip_content)[0]
        zippedFile.extractall(path_to_extract)
        return os.path.join(path_to_extract, model_asset_path)
