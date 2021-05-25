import os
import pathlib
import stat
import time
import typing as tp

from pyvcs.index import GitIndexEntry, read_index
from pyvcs.objects import hash_object
from pyvcs.refs import get_ref, is_detached, resolve_head, update_ref


def write_tree(gitdir: pathlib.Path, index: tp.List[GitIndexEntry], current_path: str = "") -> str:
    full_tree = b""
    for entry in index:
        if current_path and entry.name.find(current_path) == -1:
            continue
        curr_path_elements = current_path.split("/") if current_path else entry.name.split("/")

        if len(curr_path_elements) > 1:
            curr_dir_name = curr_path_elements[0]
            mode = "40000"
            tree_element = f"{mode} {curr_dir_name}\0".encode()
            lower_level_path = "/".join(curr_path_elements[1:])
            lower_tree_hash = bytes.fromhex(write_tree(gitdir, index, lower_level_path))
            tree_element += lower_tree_hash
        else:
            with open(entry.name, "rb") as entry_file:
                data = entry_file.read()
                sha = bytes.fromhex(hash_object(data, "blob", write=True))
            mode = str(oct(entry.mode))[2:]
            name = curr_path_elements[0]
            tree_element = f"{mode} {name}\0".encode()
            tree_element += sha
        full_tree += tree_element

    full_tree_hash = hash_object(full_tree, "tree", True)
    return full_tree_hash


def commit_tree( gitdir: pathlib.Path, tree: str, message: str, parent: tp.Optional[str] = None, author: tp.Optional[str] = None) -> str:
    timezone = get_timezone()
    timestamp = int(time.mktime(time.localtime()))

    author = author if author is not None else ""
    author_string = f"{author} {timestamp} {timezone}"
    parent_string = f"parent {parent}\n" if parent is not None else ""

    commit_data = f"tree {tree}\n" \
                       f"{parent_string}" \
                       f"author {author_string}\n" \
                       f"committer {author_string}\n" \
                       f"\n" \
                       f"{message}\n"
    return hash_object(commit_data.encode(), "commit", True)

def get_timezone():
    timezone_in_seconds = -time.timezone
    return convert_timezone_to_hours(timezone_in_seconds)

def convert_timezone_to_hours(timezone_in_seconds):
     hours =  timezone_in_seconds // 3600
     left_zeros = "0" * (2 - len(str(hours)))
     sign = "+" if hours >= 0 else "-"
     return f"{sign}{left_zeros}{hours}00"