# coding: utf-8

from qbittorrent_ark.args_parsing import get_args
from qbittorrent_ark.ark import Ark
from qbittorrent_ark.qbittorrent_logic import qbittorrent_logic_entry


def main():
    args = get_args()
    Ark(args.ark_path)
    qbittorrent_logic_entry()


if __name__ == "__main__":
    main()
