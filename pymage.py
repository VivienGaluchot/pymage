import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from PIL import Image
import hachoir.parser
import hachoir.metadata
import hachoir.core.config

import logging
logger = logging.getLogger(__name__)

hachoir.core.config.quiet = True


#-----------------
# Date extraction
#-----------------

def get_file_creation_date(path: str) -> datetime:
    return datetime.fromtimestamp(os.path.getctime(path))


def get_exif_date(path: str) -> Optional[datetime]:
    try:
        exif = Image.open(path).getexif()
        x = exif.get(36867)
        if x != None:
            return datetime.strptime(x, '%Y:%m:%d %H:%M:%S')
        else:
            return None
    except Exception:
        return None


def get_meta_data_date(path: str)-> Optional[datetime]:
    try:
        parser = hachoir.parser.createParser(path)
        if not parser:
            return None
        metadata = hachoir.metadata.extractMetadata(parser)
        if not metadata:
            logger.error("unable to extract metadata %s", path)
            return None
        for line in metadata.exportPlaintext():
            if line.startswith('- Creation date: '):
                date_str = line[len('- Creation date: '):]
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except Exception:
        return None


def get_date(path: str) -> Tuple[datetime, str]:
    exif_date = get_exif_date(path)
    if exif_date:
        return (exif_date, "exif")
    meta_date = get_meta_data_date(path)
    if meta_date:
        return (meta_date, "meta")
    return (get_file_creation_date(path), "file")


#-----------------
# Renaming
#-----------------

def get_renamed_path(path: str, date: datetime, index: int) -> str:
    date_str = date.strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(path)[1]
    if index == 0:
        renamed = f"{date_str}{ext}"
    else:
        renamed = f"{date_str}_{index}{ext}"
    return os.path.join(os.path.dirname(path), renamed)


# def rename(path: str, date: datetime, source: str) -> Optional[str]:
#     # dont trust OS file date for renaming
#     if source == "file":
#         return None

#     date_str = date.strftime("%Y%m%d_%H%M%S")

#     renamed = "{}{}".format(date_str, os.path.splitext(path)[1])
#     renamed_path = os.path.join(os.path.dirname(path), renamed)
#     # while path != renamed_path and os.path.isfile(renamed_path):
#     #     ctr += 1
#     #     renamed = "{}_{}{}".format(date_str, ctr, os.path.splitext(path)[1])
#     #     renamed_path = os.path.join(os.path.dirname(path), renamed)

#     if path != renamed_path:
#         return renamed_path
#     return None


def rename_all(folder: str):
    folder = os.path.abspath(folder)
    print("----------" + "-" * len(folder))
    print("Rename in {}".format(folder))
    print("----------"+ "-" * len(folder))

    print("Listing files...")

    occupied_file_paths: Set[str] = set()

    input_file_paths = []
    for dirpath, _dirnames, filenames in os.walk(folder):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            input_file_paths.append(file_path)
            occupied_file_paths.add(file_path)
    input_file_paths.sort()

    print("Parsing files...")

    renames: List[Tuple[str, str]] = []
    for i, path in enumerate(input_file_paths):
        date, source = get_date(path=path)
        if source == "file":
            print(f"[{i + 1}/{len(input_file_paths)}] {path} -> date not found")
        else:
            # get free renamed filename
            index = 0
            renamed = get_renamed_path(path=path, date=date, index=index)
            while renamed != path and renamed in occupied_file_paths:
                index += 1
                renamed = get_renamed_path(path=path, date=date, index=index)
            if renamed == path:
                print(f"[{i + 1}/{len(input_file_paths)}] {path} -> no operation")
            else:
                print(f"[{i + 1}/{len(input_file_paths)}] {path} -> {os.path.basename(renamed)}")
                renames.append((path, renamed))
                occupied_file_paths.add(renamed)
    
    print("Found {} files, {} to rename, execute ? (y/n)".format(len(input_file_paths), len(renames)))
    if input("") != "y":
        return
    
    for src, target in renames:
        try:
            os.rename(src, target)
            print(f"[renamed] {src} -> {renamed}")
        except Exception:
            logger.exception("rename failed")
            print(f"[failed] {src} -> {renamed}")


#-----------------
# Main
#-----------------

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) > 0:
        rename_all(folder=args[0])
