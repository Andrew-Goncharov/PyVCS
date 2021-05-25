import hashlib
import os
import pathlib
import re
import stat
import typing as tp
import zlib

from pyvcs.refs import update_ref
from pyvcs.repo import repo_find


def hash_object(data: bytes, fmt: str, write: bool = False) -> str:
    header = f"{fmt} {len(data)}\0".encode()
    store = header + data
    hash = hashlib.sha1(store).hexdigest()

    if write:
        folder_name = hash[:2]
        file_name = hash[2:]
        repo_path = repo_find()

        folder_path = repo_path / "objects" / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / file_name

        with open(file_path, "wb") as file:
            file.write(zlib.compress(store))

    return hash


def resolve_object(obj_name: str, gitdir: pathlib.Path) -> tp.List[str]:
    if len(obj_name) < 4 or len(obj_name) > 40:
        raise ValueError(f"Not a valid object name {obj_name}")

    folder_path = gitdir / "objects" / obj_name[:2]
    if not folder_path.exists() or folder_path.is_file():
        raise ValueError(f"Not a valid object name {obj_name}")

    file_hashes = []
    for file_path in folder_path.glob(f"{obj_name[2:]}*"):
        file_hashes.append(obj_name[:2] + file_path.name)

    if len(file_hashes) == 0:
        raise ValueError(f"Not a valid object name {obj_name}")

    return file_hashes


def find_object(obj_name: str, gitdir: pathlib.Path) -> str:
    # PUT YOUR CODE HERE
    ...

def read_object(sha: str, gitdir: pathlib.Path) -> tp.Tuple[str, bytes]:
    obj_path = gitdir / "objects" / sha[:2] / sha[2:]
    with obj_path.open(mode="rb") as f:
        content = zlib.decompress(f.read())
        cont_delimiter = content.find(b"\x00")
        header = content[:cont_delimiter]
        head_delimiter = header.find(b" ")
        fmt = str(header[:head_delimiter].decode("ascii"))
        decode_content = content[cont_delimiter + 1:]
    return (fmt, decode_content)

def read_tree(data: bytes):
    shas_enc, data_without_sha_enc = pop_sha(data)
    shas = list(map(lambda x: x.hex(), shas_enc))
    data_without_sha = data_without_sha_enc.decode()
    sep_data_raw = data_without_sha.split(' ')
    sep_data = list(filter(lambda x: x != '', sep_data_raw))

    permissions_raw = sep_data[::2]
    permissions = list(map(lambda x: '0' * (6 - len(x)) + x, permissions_raw))

    names = sep_data[1::2]
    return [permissions, shas, names]

def pop_sha(data):
    shas = []
    zero_byte = data.find(b'\0')
    while zero_byte != -1:
        shas.append(data[zero_byte + 1:zero_byte + 21])
        data = data[:zero_byte] + b' ' + data[zero_byte + 21:]
        zero_byte = data.find(b'\0', zero_byte + 1)

    return shas, data

def cat_file(obj_name: str, pretty: bool = True) -> None:
    gitdir = repo_find()
    shas = resolve_object(obj_name, gitdir)
    if len(shas) > 1:
        raise Exception("Provide a longer name")
    sha = shas[0]
    obj_type, obj_content_bytes = read_object(sha, gitdir)
    if obj_type == "tree":
        permissions, shas, names = read_tree(obj_content_bytes)
        resulting_string = ""
        for i in range(len(shas)):
            perm = permissions[i]
            sha = shas[i]
            name = names[i]
            type = "tree" if perm == "040000" else "blob"
            resulting_string += f"{perm} {type} {sha}\t{name}\n"
        if pretty:
            print(resulting_string)
    else:
        obj_content_decoded = obj_content_bytes.decode("ascii")
        if pretty:
            print(obj_content_decoded)


def find_all_files_from_commit_sha(gitdir: pathlib.Path, commit_sha:str):
    tree_sha = get_tree_sha_from_commit(gitdir, commit_sha)
    child_files = list(zip(*find_tree_files(gitdir, tree_sha, pathlib.Path(''))))
    parent_sha = find_commit_parent(gitdir, commit_sha)
    if parent_sha is not None:
        all_files = child_files.copy()
        parent_files = find_all_files_from_commit_sha(gitdir, parent_sha)
        for i in range(len(parent_files)):
            parent_file = parent_files[i]
            parent_file_sha = parent_file[0]
            for child_file_sha, _ in child_files:
                if parent_file_sha == child_file_sha:
                    break
            else:
                all_files.append(parent_file)
    else:
        all_files = child_files
    return all_files

def find_tree_files(gitdir: pathlib.Path, tree_sha:str, sub_obj_root: pathlib.Path) -> tp.Tuple[tp.List, tp.List]:
    tree_in_bytes = read_object(tree_sha, gitdir)[1]
    all_tree_files = []
    all_tree_files_sha = []
    for sub_obj_permissions, sub_obj_sha, sub_obj_name in zip(*read_tree(tree_in_bytes)):
        all_tree_files_sha.append(sub_obj_sha)
        full_obj_path = sub_obj_root / sub_obj_name
        all_tree_files.append(full_obj_path)
        if sub_obj_permissions == '040000':
            deeper_files_sha, deeper_files = find_tree_files(gitdir, sub_obj_sha, full_obj_path)
            all_tree_files_sha += deeper_files_sha
            all_tree_files += deeper_files
    return (all_tree_files_sha, all_tree_files)

def get_tree_content(gitdir, tree_sha):
    tree_in_bytes = read_object(tree_sha, gitdir)[1]
    sub_obj_permissions, sub_obj_shas, sub_obj_dir_names = read_tree(tree_in_bytes)

def get_tree_sha_from_commit(gitdir: pathlib.Path, commit_sha: str):
    commit_in_bytes = read_object(commit_sha, gitdir)
    commit_decoded = commit_in_bytes[1].decode()
    tree_sha = commit_decoded.split("\n")[0].split(" ")[1]
    return tree_sha

def find_commit_parent(gitdir: pathlib.Path, commit_sha: str):
    commit_in_bytes = read_object(commit_sha, gitdir)
    commit_decoded = commit_in_bytes[1].decode()
    maybe_parent = commit_decoded.split("\n")[1].split(" ")[1]
    if len(maybe_parent) == 40:
        return maybe_parent
    return None

def get_tracked_files(gitdir: pathlib.Path):
    master_branch_path = gitdir / "refs" / "heads" / "master"
    with open(master_branch_path, "r") as file:
        master_commit_sha = file.read()
    tracked_files = list(zip(*find_all_files_from_commit_sha(gitdir, master_commit_sha)))[1]
    return tracked_files