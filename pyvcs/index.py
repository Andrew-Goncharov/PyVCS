import hashlib
import operator
import os
import pathlib
import struct
import typing as tp

from pyvcs.objects import hash_object


class GitIndexEntry(tp.NamedTuple):
    # @see: https://github.com/git/git/blob/master/Documentation/technical/index-format.txt
    ctime_s: int
    ctime_n: int
    mtime_s: int
    mtime_n: int
    dev: int
    ino: int
    mode: int
    uid: int
    gid: int
    size: int
    sha1: bytes
    flags: int
    name: str

    def pack(self) -> bytes:
        data = (self.ctime_s, self.ctime_n, self.mtime_s,
                self.mtime_n, self.dev, self.ino,
                self.mode, self.uid, self.gid,
                self.size, self.sha1, self.flags,)
        encoded_name = self.name.encode("ascii")
        packed_data = struct.pack("!LLLLLLLLLL20sH", *data) + encoded_name
        while len(packed_data) % 8 != 0:
            packed_data += b"\x00"
        return packed_data

    @staticmethod
    def unpack(data: bytes) -> "GitIndexEntry":
        while data[-1] == 0:
            data = data[:-1]
        packed_data = data[:62]
        packed_name = data[62:]
        name = str(packed_name.decode("ascii"))
        unpacked_data = list(struct.unpack("!LLLLLLLLLL20sH", packed_data)) + [name]
        return GitIndexEntry(*unpacked_data)


def read_index(gitdir: pathlib.Path) -> tp.List[GitIndexEntry]:
    path = gitdir / "index"
    if not path.is_file():
        return []

    res = []
    with path.open(mode="rb") as f:
        data = f.read()
    index_entries = struct.unpack('!i', data[8:12])[0]

    index_data = data[12:]


    for i in range(index_entries):
        while len(index_data) != 0 and index_data[0] == 0:
            index_data = index_data[1:]
        data_without_name = index_data[:62]
        name_size = int.from_bytes(data_without_name[-2:], "big")
        full_data = index_data[:62+name_size]
        index_data = index_data[62+name_size:]
        res.append(GitIndexEntry.unpack(full_data))

    return res



def write_index(gitdir: pathlib.Path, entries: tp.List[GitIndexEntry]) -> None:
    path = gitdir / "index"
    with open(path, mode="wb") as f:
        index_file_data = "DIRC".encode("ascii")
        index_file_data += b"\x00\x00\x00\x02"
        index_file_data += len(entries).to_bytes(4, "big")
        for entry in entries:
            index_file_data += entry.pack()
        sha = hashlib.sha1(index_file_data).digest()
        index_file_data += sha
        f.write(index_file_data)

def ls_files(gitdir: pathlib.Path, details: bool = False) -> None:
    index_entries = read_index(gitdir)
    if details:
        for entry in index_entries:
            string_entry = f"{str(oct(entry.mode))[2:]} {entry.sha1.hex()} 0\t{entry.name}"
            print(string_entry)
    else:
        for entry in index_entries:
            print(entry.name)


def update_index(gitdir: pathlib.Path, paths: tp.List[pathlib.Path], write: bool = True) -> None:
    index_entries = []

    gitdir_relative_paths = convert_to_relative(paths)
    gitdir_relative_paths = sorted(gitdir_relative_paths)

    for path in gitdir_relative_paths:
        with open(path, mode="rb") as file:
            file_data = file.read()
        file_hash = bytes.fromhex(hash_object(file_data, "blob", True))
        file_stat = os.stat(path)
        flags = len(str(path))
        index_class_args = (int(file_stat.st_ctime), 0, int(file_stat.st_mtime), 0, file_stat.st_dev,
                            file_stat.st_ino, file_stat.st_mode, file_stat.st_uid, file_stat.st_gid,
                            file_stat.st_size, file_hash, flags, str(path),)
        index_entry =GitIndexEntry(*index_class_args)
        index_entries.append(index_entry)

    if write:
        write_index(gitdir, index_entries)

def convert_to_relative(paths: tp.List[pathlib.Path]):
    relative_paths = []
    for path in paths:
        absolute = path.absolute()
        relative = absolute.relative_to(os.getcwd())
        relative_paths.append(relative)
    return relative_paths