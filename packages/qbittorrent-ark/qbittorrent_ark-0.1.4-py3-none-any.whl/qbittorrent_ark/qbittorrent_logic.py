# coding: utf-8

import qbittorrent
import traceback

from qbittorrent_ark.ark import Ark
from qbittorrent_ark.common import url_encode_string, url_decode_category, nice_size, unix_timestamp_to_str_time, compare_two_str_lists
from qbittorrent_ark.common import get_yes_or_no_user_choice, remove_last_slash_if_needed


class QL:
    qb: qbittorrent.Client | None = None
    t: dict[str, dict] | None = None

    @staticmethod
    def __readd_it(d: dict, torrent_hash: str) -> dict:
        ti = QL.qb.get_torrent(torrent_hash)
        res = d.copy()
        if "private" not in res:
            if "is_private" not in res:
                if "is_private" in ti:
                    is_private = ti["is_private"]
                elif "private" in ti:
                    is_private = ti["private"]
                else:
                    is_private = False
                res["is_private"] = is_private
                res["private"] = is_private
            else:
                res["private"] = res["is_private"]

        if "category" not in res:
            if "category" in ti:
                category = ti["category"]
            else:
                category = ""
            res["category"] = category

        if "comment" not in res:
            if "comment" in ti:
                comment = ti["comment"]
            else:
                comment = ""
            res["comment"] = comment

        if "added_on" not in res:
            if "added_on" in ti:
                added_on = ti["added_on"]
            elif "addition_date" in ti:
                added_on = ti["addition_date"]
            elif "addition_date" in res:
                added_on = res["addition_date"]
            else:
                added_on = 0
            res["added_on"] = added_on

        return res

    @staticmethod
    def get_torrents() -> dict[str, dict]:
        """
        :return: {hash: {
            name: str,
            tags: str,
            "save_path": str,
            "hash": str,
            "size": int,
            "total_size": int,
            "private": bool,
            "is_private": bool,
            "category": str,
            "comment": str,
            "added_on": int,
        }}
        """
        # https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-5.0)#get-torrent-generic-properties
        buff: list[dict] = QL.qb.torrents()
        res: dict[str, dict] = {}
        for buff_i in buff:
            buff_i_hash = str(buff_i["hash"])
            sad = QL.__readd_it(buff_i, buff_i_hash)
            res[buff_i_hash] = sad
        return res

    @staticmethod
    def get_torrent(torrent_hash: str) -> dict:
        # QL.qb.torrents_info(torrent_hash)  # is piece of code
        return QL.qb.get_torrent(torrent_hash)

    @staticmethod
    def get_trackers(torrent_hash: str) -> list[dict]:
        # https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-5.0)#get-torrent-trackers
        # interest only url and status
        # status decoding:
        # Value 	Description
        # 0 	Tracker is disabled (used for DHT, PeX, and LSD)
        # 1 	Tracker has not been contacted yet
        # 2 	Tracker has been contacted and is working
        # 3 	Tracker is updating
        # 4 	Tracker has been contacted, but it is not working (or doesn't send proper replies)
        tt: list[dict] = QL.qb.get_torrent_trackers(torrent_hash)
        return tt

    @staticmethod
    def get_trackers_nice(torrent_hash: str) -> list[str]:
        status_dict = {0: "Tracker is disabled (used for DHT, PeX, and LSD)",
                       1: "Tracker has not been contacted yet",
                       2: "Tracker has been contacted and is working",
                       3: "Tracker is updating",
                       4: "Tracker has been contacted, but it is not working (or doesn't send proper replies)"}
        tts = QL.get_trackers(torrent_hash)
        res = []
        for tt_i in tts:
            status_int = int(tt_i["status"])
            status = status_dict[status_int]
            buff = f"{tt_i['url']}: {status} ({status_int})"
            res.append(buff)
        return res

    # @staticmethod
    # def get_category(torrent_hash: str) -> str:
    #     return QL.t[torrent_hash]["category"]
    # @staticmethod
    # def set_category(torrent_hash: str, new_category: str):
    #     if new_category not in QL.get_all_categories():
    #         QL.create_category(new_category)
    #     QL.qb.set_category(torrent_hash, new_category)
    # @staticmethod
    # def create_category(new_category: str):
    #     QL.qb.create_category(new_category)
    # @staticmethod
    # def get_all_categories() -> list[str]:
    #     pass  # fu python-qbittorrent

    @staticmethod
    def get_torrent_tags(torrent_hash: str) -> list[str]:
        s: str = QL.t[torrent_hash]["tags"]
        res = list(map(str, s.split(',')))
        res = [item_i.strip() for item_i in res]
        return [url_decode_category(tag_i) for tag_i in res]

    @staticmethod
    def _man_with_torrent_tags(torrent_hash: str, tags: list[str], man_code: int):
        if man_code == 0:
            _link = "addTags"
        elif man_code == 1:
            _link = "removeTags"
        else:
            raise ValueError(f"(QL._man_with_torrent_tags) man_code must be 0 or 1")

        if len(tags) < 1:
            raise ValueError(f"(QL._man_with_torrent_tags) tags contains zero items for torrent \"{torrent_hash}\". ")
        tags = [url_encode_string(tag_i) for tag_i in tags]

        host, _, __ = Ark().get_host_login_password()
        session = QL.qb.session
        url = f"{host}/api/v2/torrents/{_link}"
        headers = {
            "User-Agent": "Fiddler",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "hashes": f"{torrent_hash}",
            "tags": ",".join(tags)
        }
        response = session.post(url, headers=headers, data=data)

        if response.status_code == 200:
            pass
        else:
            print(f"(QL._man_with_torrent_tags, code={man_code}) Error:", response.status_code, response.text)

    @staticmethod
    def add_tags_to_torrent(torrent_hash: str, tags: list[str]):
        # fu python-qbittorrent
        # https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-5.0)#add-torrent-tags
        QL._man_with_torrent_tags(torrent_hash, tags, 0)

    @staticmethod
    def remove_tags_from_torrent(torrent_hash: str, tags: list[str]):
        # fu python-qbittorrent
        # https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-5.0)#remove-torrent-tags
        QL._man_with_torrent_tags(torrent_hash, tags, 1)

    @staticmethod
    def get_torrent_name(torrent_hash: str) -> str:
        return QL.t[torrent_hash]["name"]

    @staticmethod
    def set_torrent_name(torrent_hash: str, new_name: str):
        QL.qb.set_torrent_name(torrent_hash, new_name)

    @staticmethod
    def get_torrent_save_path(torrent_hash: str) -> str:
        return QL.t[torrent_hash]["save_path"]

    @staticmethod
    def set_torrent_save_path(torrent_hash: str, new_path: str):
        QL.qb.set_torrent_location(torrent_hash, new_path)

    @staticmethod
    def export_torrent_file(torrent_hash: str) -> bytes:
        session = QL.qb.session
        host, _, __ = Ark().get_host_login_password()
        url = f"{host}/api/v2/torrents/export?hash={torrent_hash}"
        response = session.get(url)
        if response.status_code == 200:
            return response.content
        else:
            print("(QL.export_torrent_file) Error:", response.status_code, response.text)


def form_record_for_ark(torrent_hash: str) -> dict:
    synk_dict = {}
    info_dict = {}
    res = {"hash": torrent_hash, "comment1": "Your comment here. Use key comment2 for multiline comment",
           "synk": synk_dict, "info": info_dict}

    t = QL.t[torrent_hash]

    synk_dict["name"] = t["name"]
    synk_dict["tags"] = ",".join(QL.get_torrent_tags(torrent_hash))
    synk_dict["path"] = t["save_path"]

    info_dict["hash"] = torrent_hash
    info_dict["hash_v2"] = t["infohash_v2"]
    info_dict["size"] = f"{nice_size(t['size'])} ({t['size']})"
    info_dict["total_size"] = f"{nice_size(t['total_size'])} ({t['total_size']})"
    if "private" not in t and "is_private" not in t:
        info_dict["private"] = False
    else:
        if "private" in t:
            info_dict["private"] = t["private"]
        elif "is_private" in t:
            info_dict["private"] = t["is_private"]
    if "category" in t:
        info_dict["category"] = t["category"]
    else:
        info_dict["category"] = ""
    if "comment" in t:
        info_dict["torrent_comment"] = t["comment"]
    else:
        info_dict["torrent_comment"] = ""
    info_dict["date"] = unix_timestamp_to_str_time(t["added_on"])
    if Ark().consider_tracker_changes():
        info_dict["trackers"] = QL.get_trackers_nice(torrent_hash)

    return res


def qbittorrent_logic_entry():
    host, username, password = Ark().get_host_login_password()

    try:
        qb = qbittorrent.Client(host)
    except Exception as e:
        error_text = f"{traceback.format_exc()}\n{e}"
        print(error_text)
        print(f"\nCannot connect to qbittorrent with API. Do you set up \"Web UI\" in qbittorrent preferences? Exiting.")
        exit(1)
    qb.login(username, password)

    QL.qb = qb
    QL.t = QL.get_torrents()
    qbittorrent_logic_process()


def qbittorrent_logic_process():
    is_changed = False
    ark = Ark()
    consider_tracker_changes = ark.consider_tracker_changes()
    t = ark.get_torrents()
    ts = QL.t

    indexer = {}
    for t_i in t:
        indexer[t_i["hash"]] = t_i

    for t_i in ts:
        if t_i not in indexer:
            record = form_record_for_ark(t_i)
            is_changed = True
            print(f"New torrent detected: {t_i}")
            t.append(record)

    indexer = {}
    for t_i in t:
        indexer[t_i["hash"]] = t_i

    torrent_file_export_dir = ark.get_torrent_file_export_dir()
    if not (torrent_file_export_dir is None):
        for ts_i in ts:
            file_name = f"{ts_i}.torrent"
            file = torrent_file_export_dir / file_name
            if not file.exists():
                torrent_file_content = QL.export_torrent_file(ts_i)
                with open(file, 'wb') as fd:
                    fd.write(torrent_file_content)
                    fd.flush()
                print(f"({ts_i}) torrent file is exported. ")

    for ts_i in ts:
        ts_i_hash = ts_i
        record = indexer[ts_i_hash]["synk"]

        ts_i_name = QL.get_torrent_name(ts_i_hash)
        if ts_i_name != record["name"]:  # NAME
            print(f"({ts_i_hash}) Changing name from \"{ts_i_name}\" to \"{record['name']}\"")
            QL.set_torrent_name(ts_i_hash, record["name"])

        ts_i_tags = QL.get_torrent_tags(ts_i_hash)
        t_i_tags = list(record["tags"].split(","))
        t_i_tags = [el_i.strip() for el_i in t_i_tags]
        if not compare_two_str_lists(ts_i_tags, t_i_tags, True):  # TAGS
            print(f"({ts_i_hash}) Changing tags from {ts_i_tags} to {t_i_tags}")
            QL.remove_tags_from_torrent(ts_i_hash, ts_i_tags)
            QL.add_tags_to_torrent(ts_i_hash, t_i_tags)

        ts_i_path = QL.get_torrent_save_path(ts_i_hash)
        t_i_path = remove_last_slash_if_needed(record["path"])
        if ts_i_path != t_i_path:  # PATH
            print(f"({ts_i_hash}) Changing location from \"{ts_i_path}\" to \"{t_i_path}\"")
            QL.set_torrent_save_path(ts_i_hash, t_i_path)

        if consider_tracker_changes:
            ts_i_trackers = QL.get_trackers_nice(ts_i_hash)
            if "trackers" not in indexer[ts_i_hash]["info"]:
                indexer[ts_i_hash]["info"]["trackers"] = []
            t_i_trackers = indexer[ts_i_hash]["info"]["trackers"]
            if not compare_two_str_lists(ts_i_trackers, t_i_trackers, True):  # TRACKERS
                print(f"({ts_i_hash}) Trackers or trackers state changed. Change \"consider_tracker_changes\" to \"false\" in ark file, if no need check trackers. ")
                indexer[ts_i_hash]["info"]["trackers"] = ts_i_trackers
                is_changed = True

    is_sorted = False
    try:
        t, is_sorted = ark.sort_by(t, ark.get_sorted_parameter())
    except Exception as e:
        error_text = f"{traceback.format_exc()}"
        print(error_text)
    if is_sorted:
        is_changed = True
        print(f"Torrents were sorted by \"{ark.get_sorted_parameter()}\"")

    if is_changed:
        prefix = f"New changes detected with ark. Do you want to save it (it will change your current ark file \"{ark.get_path()}\")?"
        user_choice = get_yes_or_no_user_choice(prefix)
        if user_choice:
            ark.set_torrents(t)
            ark.save()
            print("Saved! ")
        else:
            print(f"\nArk file \"{ark.get_path()}\" not changed. Exiting.")
