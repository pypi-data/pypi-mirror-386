# coding: utf-8

import argparse
from qbittorrent_ark import __version__


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="qbittorrent_ark is gui-less qbittorrent manipulation. ")

    parser.add_argument("--version", action="version", version=f"V{__version__}", help="Check version. ")

    parser.add_argument("ark_path", type=str, help="Path to yaml file with ark. If file does not exists, it will be created. ")

    return parser.parse_args()
