from os import listdir, rename
from pathlib import Path


def file_count(tpath: Path):
    files: list = [f for f in Path(tpath).iterdir() if f.is_file()]
    if files:
        return len(files)
    return 0


def dir_count(tpath: Path):
    dirs: list = [d for d in Path(tpath).iterdir() if d.is_dir()]
    if tpath:
        return len(dirs)
    return 0


def sub_del(tpath: Path):
    for sub in tpath.iterdir():
        if sub.is_dir():
            sub_del(sub)
        if sub.is_file():
            sub.unlink()
    tpath.rmdir()


# def sub_fix(tpath: Path):
#     for df in listdir(tpath):
#         origin_path: Path = Path(f"{tpath}/{df}").resolve()

#         if origin_path.is_file():
#             rename(origin_path, f"{tpath}/{df.replace(' ', '_')}")

#         if origin_path.is_dir():
#             sub_fix(origin_path)
#             rename(origin_path, f"{tpath}/{df.replace(' ', '_')}")
