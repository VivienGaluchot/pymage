import hashlib
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

def get_signature(path: str) -> str:
    sha1 = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha1.update(chunk)
    return sha1.hexdigest()

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
    


class FileResource:
    # initial path of file
    path: str
    date: datetime
    date_source: str
    signature: str

    def __init__(self, path: str):
        self.path = path
        self.date, self.date_source = get_date(path=path)
        self.signature = get_signature(path=path)
    
    def renamed_path(self, occupied_file_paths: Set[str], is_removed: bool) -> str:
        if self.date_source == "file":
            renamed = self.path
        else:
            index = 0
            renamed = get_renamed_path(path=self.path, date=self.date, index=index)
            while renamed != self.path and renamed in occupied_file_paths:
                index += 1
                renamed = get_renamed_path(path=self.path, date=self.date, index=index)
        if is_removed:
            base, ext = os.path.splitext(renamed)
            renamed = f"{base}.rm{ext}"
        return renamed


def rename_all(folder: str):
    folder = os.path.abspath(folder)
    print("----------" + "-" * len(folder))
    print("Rename in {}".format(folder))
    print("----------"+ "-" * len(folder))

    print("Listing files...")

    paths = []
    for dirpath, _, filenames in os.walk(folder):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            paths.append(file_path)
    paths.sort()

    print("Parsing files...")

    resources : List[FileResource] = []
    for i, path in enumerate(paths):
        resource = FileResource(path=path)
        if resource.date_source == "file":
            print(f"[{i + 1}/{len(paths)}] {path} - date not found")
        else:
            print(f"[{i + 1}/{len(paths)}] {path} - {resource.date}")
        resources.append(resource)

    print("Solving...")

    occupied_file_paths: Set[str] = set(paths)
    renames: List[Tuple[FileResource, str]] = []
    signatures: Set[str] = set()
    for resource in resources:
        # removes
        is_removed = resource.signature in signatures
        signatures.add(resource.signature)
        # renames
        renamed = resource.renamed_path(occupied_file_paths=occupied_file_paths, is_removed=is_removed)
        if renamed != resource.path:
            print(f"[rename] {resource.path} -> {renamed}")
            renames.append((resource, renamed))
            occupied_file_paths.add(renamed)
    
    print("Found {} files, {} to rename, execute ? (y/n)".format(len(paths), len(renames)))
    if input("") != "y":
        return
    
    for resource, target in renames:
        try:
            os.rename(resource.path, target)
            print(f"[renamed] {resource.path} -> {renamed}")
        except Exception:
            logger.exception("rename failed")
            print(f"[failed] {resource.path} -> {renamed}")


#-----------------
# Main
#-----------------

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) > 0:
        rename_all(folder=args[0])
