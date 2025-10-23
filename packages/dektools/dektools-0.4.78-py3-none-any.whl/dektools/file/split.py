import os
import math
import hashlib
from ..func import FuncAnyArgs
from .path import normal_path
from .operation import remove_path, read_file, sure_dir


def split_file(path, limit=None, clear=False, chunked_size=64 * 2 ** 10, out=None):
    size = os.stat(path).st_size
    count = 1 if limit is None else math.ceil(size / limit)
    chunked_size = min(chunked_size, limit)
    hs = hashlib.sha256()
    if out:
        sure_dir(out)
        out = os.path.join(out, os.path.basename(path))
    else:
        out = path
    with open(path, 'rb') as file:
        for i in range(count):
            with open(pack_split_name(out, i + 1), 'wb') as f:
                total = 0
                for chunk in iter(lambda: file.read(chunked_size), b""):
                    total += chunked_size
                    f.write(chunk)
                    hs.update(chunk)
                    if total + chunked_size > limit:
                        rest = limit - total
                        if rest > 0:
                            chunk = file.read(rest)
                            f.write(chunk)
                            hs.update(chunk)
                        break
    with open(pack_split_name(out, 0), 'wb') as f:
        f.write(size.to_bytes(8, 'big', signed=False))
        f.write(hs.digest())
    if clear:
        remove_path(path)
    return out, count


def pack_split_name(base, index):
    if callable(base):
        return base(index)
    return f"{base}.{index}"


def base_split_name(name):
    return name.rsplit('.', 1)[0]


def meta_split_file(path):
    if callable(path):
        getter = path
    else:
        def getter(index):
            try:
                return f"{normal_path(path)}.{index}"
            except FileNotFoundError:
                return None
    getter = FuncAnyArgs(getter)
    path_meta = getter(0, pack_split_name)
    if path_meta is None:
        raise FileNotFoundError(f"Can't find meta file: `{path_meta}`")
    bs = read_file(path_meta)
    total_size = int.from_bytes(bs[:8], 'big', signed=False)
    i = 1
    size = 0
    parts = []
    while size < total_size:
        path_part = getter(i, pack_split_name)
        if not path_part:
            raise FileNotFoundError(f"Can't find part file: `{path_part}`")
        size_part = os.stat(path_part).st_size
        parts.append(path_part)
        size += size_part
        i += 1
    if size > total_size:
        raise ValueError(f"Can't match total size: {size} > {total_size}")
    return parts, bs[8:].hex(), total_size, path_meta


def remove_split_files(path):
    parts, _, _, path_meta = meta_split_file(path)
    remove_path(path_meta)
    for path_part in parts:
        remove_path(path_part)


def combine_split_files(path, clear=False, chunked_size=64 * 2 ** 10, out=None):
    parts, checksum_correct, _, path_meta = meta_split_file(path)
    if parts:
        target = base_split_name(path_meta)
        if out:
            sure_dir(out)
            out = os.path.join(out, os.path.basename(target))
        else:
            out = target
        hs = hashlib.sha256()
        with open(out, 'wb') as file:
            if clear:
                remove_path(path_meta)
            for path_part in parts:
                with open(path_part, 'rb') as f:
                    for chunk in iter(lambda: f.read(chunked_size), b""):
                        file.write(chunk)
                        hs.update(chunk)
                if clear:
                    remove_path(path_part)
        checksum = hs.hexdigest()
        if checksum != checksum_correct:
            raise ValueError(f"Can't match Crc results: {checksum} != {checksum_correct}")
        return out


def fetch_split_files(url, out=None, username=None, password=None, **kwargs):
    from ..download import download_from_http
    from ..web.url import Url
    from ..file import clear_dir, sure_dir, write_file

    def getter(index, pack):
        _url = pack(url, index)
        return download_from_http(
            _url, os.path.join(out, Url.new(_url).filename), username=username, password=password
        )

    if out:
        clear_dir(sure_dir(out))
    else:
        out = write_file(None)
    return combine_split_files(getter, clear=True, out=out, **kwargs)
