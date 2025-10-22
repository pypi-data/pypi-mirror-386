from typing import Dict

from ._utils import get_extension, CompatibilityUnpickler
from .parser import (
    read_star,
    read_tsv,
    read_txt,
    read_mesh,
    read_volume,
    read_tsi,
    read_vtu,
    read_structure,
    GeometryDataContainer,
)

FORMAT_MAPPING = {
    read_star: ["star"],
    read_tsv: ["tsv"],
    read_txt: ["txt", "xyz", "csv"],
    read_mesh: ["obj", "ply", "stl", "off", "gltf", "glb," "fbx"],
    read_volume: ["mrc", "em", "map", "h5", "mrc.gz", "em.gz", "map.gz"],
    read_tsi: ["q", "tsi"],
    read_vtu: ["vtu"],
    read_structure: ["pdb", "cif", "gro"],
}


def open_file(filename: str, *args, **kwargs) -> GeometryDataContainer:
    """
    Open and parse a file based on its extension.

    Parameters
    ----------
    filename : str
        Path to the file to be opened.
    *args
        Additional positional arguments passed to the parser function.
    **kwargs
        Additional keyword arguments passed to the parser function.

    Returns
    -------
    GeometryDataContainer
        Parsed geometry data container.

    Raises
    ------
    ValueError
        If the file extension is not supported.
    """
    extension = get_extension(filename)[1:]

    func = None
    for reader_func, reader_formats in FORMAT_MAPPING.items():
        if extension not in reader_formats:
            continue
        func = reader_func

    if func is None:
        supported = ", ".join([f"'{x}'" for t in FORMAT_MAPPING.values() for x in t])
        raise ValueError(f"Unknown extension '{extension}', supported are {supported}.")
    return func(filename, *args, **kwargs)


def open_session(filename: str, *args, **kwargs) -> Dict:
    """
    Open and deserialize a pickled session file.

    Parameters
    ----------
    filename : str
        Path to the session file to be opened.
    *args
        Additional positional arguments (unused).
    **kwargs
        Additional keyword arguments (unused).

    Returns
    -------
    Dict
        Deserialized session data.
    """
    with open(filename, "rb") as ifile:
        unpickler = CompatibilityUnpickler(ifile)
        data = unpickler.load()
    return data
