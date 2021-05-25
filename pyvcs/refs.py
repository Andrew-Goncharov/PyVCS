import pathlib
import typing as tp


def update_ref(gitdir: pathlib.Path, ref: tp.Union[str, pathlib.Path], new_value: str) -> None:
    if ref == "HEAD":
        ref_path = get_ref(gitdir)
    else:
        ref_path = ref
    with open(gitdir / ref_path, "w") as ref_file:
        ref_file.write(new_value)


def symbolic_ref(gitdir: pathlib.Path, name: str, ref: str) -> None:
    with open(gitdir / name, "w") as ref_file:
        ref_file.write(ref)


def ref_resolve(gitdir: pathlib.Path, refname: str) -> str:
    if refname == "HEAD":
        ref_path = get_ref(gitdir)
    else:
        ref_path = refname
    with open(gitdir / ref_path, "r") as ref_file:
        return ref_file.read()


def resolve_head(gitdir: pathlib.Path) -> tp.Optional[str]:
    head_branch_path = get_ref(gitdir)
    if not (gitdir / pathlib.Path(head_branch_path)).exists():
        return None
    else:
        with open(gitdir / head_branch_path, "r") as head_branch_file:
            head_branch_data = head_branch_file.read()
        return head_branch_data


def is_detached(gitdir: pathlib.Path) -> bool:
    head_path = gitdir / "HEAD"
    with open(head_path, "rb") as head_file:
        head_data = head_file.read()
    if head_data[:3] == b"ref":
        return False
    return True


def get_ref(gitdir: pathlib.Path) -> str:
    head_path = gitdir / "HEAD"
    with open(head_path, "rb") as head_file:
        head_data = head_file.read()
    if head_data[:3] == b"ref":
        head_path = head_data[5:].decode().rstrip()
        return head_path
    else:
        return head_data.hex()