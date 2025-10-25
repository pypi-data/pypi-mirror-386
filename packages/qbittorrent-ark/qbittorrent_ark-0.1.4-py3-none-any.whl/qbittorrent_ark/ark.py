# coding: utf-8

import yaml
from collections import OrderedDict
from pathlib import Path
from ksupk import singleton_decorator

from qbittorrent_ark.common import compare_two_str_lists


@singleton_decorator
class Ark:
    def __init__(self, path: Path | str):
        self.current_version = "1"

        if isinstance(path, str):
            self.path = Path(path)
        elif isinstance(path, Path):
            self.path = path
        else:
            raise ValueError(f"(Ark.__init__) path must be str or pathlib.Path")

        if self.path.exists():
            with open(self.path, 'r', encoding="utf-8") as file:
                data = yaml.safe_load(file)
            self.data: dict = dict(data)
            if self.data["version"] != self.current_version:
                print(f"Current version of your ark yaml file \"{self.path}\" is \"{self.data['version']}\", current is \"{self.current_version}\". Upgrade your ark yaml file or downgrade qbittorrent_ark.")
                exit(1)
            self.client_data = self.data["settings"]["client"]
        else:
            self._create_yaml_template()

    def _create_yaml_template(self):
        print(f"No yaml-file detected on \"{self.path}\". Creating new...")

        data = {"version": self.current_version,
                "settings": {
                    "client": {"host": "url to host. For example: http://localhost:8080", "login": "your_login_here", "password": "your_secrect_password_here"},
                    "app": {
                        "torrent_file_export_dir": "path to directory, where torrent files will be exported. Leve it empty (\"\") if no needed.",
                        "sort_by": "- Sort torrents by the specified parameter. For example, if synk/name is specified, the torrents will be sorted by name. "
                                   "If this string begins with \"-\", no sorting will be applied."
                                   "If this string begins with \"+\", reverse sorting will be applied.",
                        "consider_tracker_changes": False,
                    },
                },
                "torrents": []}

        self.data = data
        self.save()

        print(f"Created. Set up it: \"{self.path}\" -- and run again. \nExiting.")
        exit()

    def get_host_login_password(self) -> tuple[str, str, str]:
        return self.client_data["host"], self.client_data["login"], self.client_data["password"]

    def get_torrents(self) -> list:
        """
        hash
        comment
        synk:
            name
            tags
            path
        info:
            hash
            hash_v2
            size
            total_size
            private
            category
            torrent_comment
            date
            trackers
        """
        return self.data["torrents"]

    def set_torrents(self, torrents: list):
        self.data["torrents"] = torrents

    def save(self):
        with open(self.path, 'w', encoding="utf-8") as file:
            yaml.dump(dict(OrderedDict(self.data)), file, allow_unicode=True, default_flow_style=False, sort_keys=False, width=float("inf"))

    def get_path(self) -> Path:
        return self.path

    def get_torrent_file_export_dir(self) -> Path | None:
        if self.data["settings"]["app"]["torrent_file_export_dir"].strip() == "":
            return None
        res = Path(self.data["settings"]["app"]["torrent_file_export_dir"])
        res.mkdir(parents=True, exist_ok=True)
        return res

    def sort_by(self, torrents: list, key_str: str) -> tuple[list, bool]:
        key = key_str.strip().lower()
        if key[0] == "-":
            return torrents, False
        if key[0] == "+":
            _reversed = True
            key = key[1:]
        else:
            _reversed = False
            key = key

        def find_int_content_in_parentheses(s: str) -> int:
            # pattern = r'$.*(\d+)$'  # fu re
            s = s.strip()
            begin, end = s.rindex("("), s.rindex(")")
            return int(s[begin+1:end])

        def tags_to_str(tags: str) -> str:
            res = tags.split(",")
            res = [el_i.strip() for el_i in res]
            return ",".join(res)

        fu = {
            "hash": lambda x: x["hash"],
            "synk/name": lambda x: x["synk"]["name"],
            "synk/tags": lambda x: tags_to_str(x["synk"]["tags"]),
            "synk/path": lambda x: x["synk"]["path"],
            "info/hash": lambda x: x["info"]["hash"],
            "info/hash_v2": lambda x: x["info"]["hash_v2"],
            "info/size": lambda x: find_int_content_in_parentheses(x["info"]["size"]),
            "info/total_size": lambda x: find_int_content_in_parentheses(x["info"]["total_size"]),
            "info/private": lambda x: x["info"]["private"],
            "info/category": lambda x: x["info"]["category"],
            "info/torrent_comment": lambda x: x["info"]["torrent_comment"],
            "info/date": lambda x: find_int_content_in_parentheses(x["info"]["date"]),
        }
        if key not in fu:
            raise ValueError(f"(Ark.sort_by) \"sort_by\" key must be only one of {list(fu.keys())}, not \"{key_str}\"")

        hashes_before = [el_i["hash"] for el_i in torrents]
        torrents_sorted = sorted(torrents, key=fu[key], reverse=_reversed)
        hashes_after = [el_i["hash"] for el_i in torrents_sorted]

        return torrents_sorted, not compare_two_str_lists(hashes_before, hashes_after, False)

    def get_sorted_parameter(self) -> str:
        return self.data["settings"]["app"]["sort_by"]

    def consider_tracker_changes(self) -> bool:
        return self.data["settings"]["app"]["consider_tracker_changes"]
