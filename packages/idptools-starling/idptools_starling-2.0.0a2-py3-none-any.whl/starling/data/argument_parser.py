import yaml


def get_params(config_file: str = None) -> dict:
    """
    A function that reads the default configuration file
    and merges it with the user configuration file.

    Parameters
    ----------
    config_file : str, optional
        A path to the user configuration file, by default None

    Returns
    -------
    dict
        A dictionary containing the configuration parameters
    """
    with open(config_file, "r") as stream:
        user_config = yaml.safe_load(stream)

    return user_config


def get_vae_params(config_file: str) -> dict:
    """
    A function that reads the default configuration file
    and merges it with the user configuration file.

    Parameters
    ----------
    config_file : str, optional
        A path to the user configuration file, by default None

    Returns
    -------
    dict
        A dictionary containing the configuration parameters
    """

    with open(config_file, "r") as stream:
        user_config = yaml.safe_load(stream)

    return user_config
