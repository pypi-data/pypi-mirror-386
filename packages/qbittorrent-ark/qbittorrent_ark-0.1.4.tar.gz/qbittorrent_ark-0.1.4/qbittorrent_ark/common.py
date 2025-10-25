# coding: utf-8

import datetime
import urllib.parse


def url_encode_string(s: str) -> str:
    """URL-encode the string."""
    return urllib.parse.quote(s)


def url_decode_category(s: str) -> str:
    """URL-decode the category name."""
    return urllib.parse.unquote(s)


def nice_size(size: int) -> str:
    units = ['b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
    index = 0

    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1

    return f"{size:.2f} {units[index]}"


def unix_timestamp_to_str_time(unix_timestamp: int) -> str:
    dt = datetime.datetime.fromtimestamp(unix_timestamp)

    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
    return f"{formatted_time} ({unix_timestamp})"


def compare_two_str_lists(a: list[str], b: list[str], sorting: bool) -> bool:
    if len(a) != len(b):
        return False
    else:
        # return "".join(sorted(a)) == "".join(sorted(b))
        if sorting:
            a, b = sorted(a), sorted(b)
        for i in range(len(a)):
            if a[i] != b[i]:
                return False
        return True


def get_yes_or_no_user_choice(prefix: str) -> bool:
    while True:
        print(f"{prefix} (y/n) ", end="")
        user_input = input()
        c = user_input.strip().lower()
        if c in ["yes", "y", "1", "yep"]:
            return True
        elif c in ["no", "n", "0", "nein"]:
            return False
        else:
            print(f"Cannot understand \"{user_input}\". Please try again. ")


def remove_last_slash_if_needed(url: str) -> str:
    if len(url) == 1:
        return url
    while url[-1] == "/":
        url = url[:-1]
    return url
