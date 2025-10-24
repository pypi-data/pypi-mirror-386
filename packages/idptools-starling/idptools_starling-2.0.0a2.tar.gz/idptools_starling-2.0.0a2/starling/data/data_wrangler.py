from typing import Iterator, Tuple

import h5py
import hdf5plugin
import numpy as np
import pandas as pd


def one_hot_encode(sequences):
    """
    One-hot encodes a sequence.
    """
    # Define the mapping of each amino acid to a unique integer
    aa_to_int = {
        "0": 0,
        "A": 1,
        "C": 2,
        "D": 3,
        "E": 4,
        "F": 5,
        "G": 6,
        "H": 7,
        "I": 8,
        "K": 9,
        "L": 10,
        "M": 11,
        "N": 12,
        "P": 13,
        "Q": 14,
        "R": 15,
        "S": 16,
        "T": 17,
        "V": 18,
        "W": 19,
        "Y": 20,
    }

    # Convert sequences to numpy array of integers
    int_sequences = [[aa_to_int[aa] for aa in sequence] for sequence in sequences]
    int_sequences = np.array(int_sequences)

    # Create an array of zeros with shape (num_sequences, sequence_length, num_classes)
    num_sequences = len(sequences)
    sequence_length = max(len(sequence) for sequence in sequences)
    num_classes = len(aa_to_int)

    one_hot_encoded_seq = np.zeros(
        (num_sequences, sequence_length, num_classes), dtype=np.float32
    )

    # Use advanced indexing to set the appropriate elements to 1
    for i, sequence in enumerate(int_sequences):
        one_hot_encoded_seq[i, np.arange(len(sequence)), sequence] = 1

    return one_hot_encoded_seq


def MaxPad(original_array: np.array, shape: tuple) -> np.array:
    """
    A function that takes in a distance map and pads it to a desired shape

    Parameters
    ----------
    original_array : np.array
        A distance map

    Returns
    -------
    np.array
        A distance map padded to a desired shape
    """
    # Pad the distance map to a desired shape
    pad_height = max(0, shape[0] - original_array.shape[0])
    pad_width = max(0, shape[1] - original_array.shape[1])
    return np.pad(
        original_array,
        ((0, pad_height), (0, pad_width)),
        mode="constant",
        constant_values=0,
    )


def load_hdf5_compressed(file_path, frame=None, keys_to_load=None):
    """
    Loads data from an HDF5 file, optionally for a specific frame.

    Parameters:
        - file_path (str): Path to the HDF5 file.
        - frame (int, optional): Specific frame to load from 'dm' or 'latents'. If None, loads full datasets.
        - keys_to_load (list, optional): Specific dataset keys to load. If None, loads all available keys.

    Returns:
        - dict: {key: np.ndarray or np.ndarray slice}
    """
    special_keys = {"dm", "latents"}
    data = {}

    with h5py.File(file_path, "r") as f:
        keys = keys_to_load if keys_to_load is not None else list(f.keys())
        for key in keys:
            dataset = f[key]
            if frame is not None and key in special_keys and dataset.shape[0] > frame:
                data[key] = dataset[frame]
            else:
                data[key] = dataset[()]
    return data


def read_tsv_file(tsv_file: str) -> Iterator[Tuple[str, str]]:
    """
    A function that reads the paths to distance maps from a tsv file

    Parameters
    ----------
    tsv_file : str
        A path to a tsv file containing the paths to distance maps as a first column
        and index of a distance map to load as a second column

    Returns
    -------
    Iterator[Tuple[str, str]]
        An iterator of tuples containing paths to distance maps and their indices
    """
    df = pd.read_csv(tsv_file, sep="\t", header=None, usecols=[0, 1])
    return df


def symmetrize(matrix):
    """
    Symmetrizes a matrix.
    """
    if np.array_equal(matrix, matrix.T):
        return matrix
    else:
        # Extract upper triangle excluding diagonal
        upper_triangle = np.triu(matrix, k=1)
        # Symmetrize upper triangle by mirroring
        sym_matrix = upper_triangle + upper_triangle.T
        # Add diagonal elements (to handle odd-sized matrices)
        sym_matrix += np.diag(np.diag(matrix))
        return sym_matrix
