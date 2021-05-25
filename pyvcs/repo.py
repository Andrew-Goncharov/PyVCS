import os
import pathlib
import typing as tp


def get_repo_name() -> str:
    return os.environ.get("GIT_DIR", ".git")


def repo_find(workdir: tp.Union[str, pathlib.Path] = ".") -> pathlib.Path:
    workdir = pathlib.Path(workdir)
    repo_name = get_repo_name()

    curr_path = workdir.absolute()
    while curr_path != curr_path.root:
        repo_path = curr_path / repo_name
        if repo_path.is_dir():
            return repo_path

    raise ValueError("Repo doesn't exist")


def repo_create(workdir: tp.Union[str, pathlib.Path]) -> pathlib.Path:
    workdir = pathlib.Path(workdir)

    if workdir.is_file():
        raise ValueError(f"{workdir.name} is not a directory")

    repo_path = workdir / get_repo_name()

    if repo_path.is_file():
        raise ValueError(f"{repo_path.name} is not a directory")

    if repo_path.is_dir():
        return repo_path

    repo_path.mkdir()
    (repo_path / "refs" / "heads").mkdir(parents=True)
    (repo_path / "refs" / "tags").mkdir(parents=True)
    (repo_path / "objects").mkdir(parents=True)

    head_path = repo_path / "HEAD"
    with open(head_path, "w") as file:
        file.write("ref: refs/heads/master\n")

    config_path = repo_path / "config"
    with open(config_path, "w") as file:
        file.write("[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n\tlogallrefupdates = false\n")

    description_path = repo_path / "description"
    with open(description_path, "w") as file:
        file.write("Unnamed pyvcs repository.\n")

    return repo_path
