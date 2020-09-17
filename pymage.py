import os
import datetime
import sys

from PIL import Image

from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

import logging
logger = logging.getLogger(__name__)


#-----------------
# Date extraction
#-----------------

def get_file_date(path):
    return datetime.datetime.fromtimestamp(os.path.getctime(path))


def get_exif_date(path):
    try:
        exif = Image.open(path).getexif()
        if exif.get(36867) != None:
            return datetime.datetime.strptime(exif.get(36867), '%Y:%m:%d %H:%M:%S')
        else:
            return None
    except Image.UnidentifiedImageError as e:
        return None
    except Exception as e:
        logger.exception("cant get exif date")
        return None


def get_meta_data_date(path):
    parser = createParser(path)
    if not parser:
        logger.error("unable to parse file", path)
        return None
    try:
        metadata = extractMetadata(parser)
    except Exception as err:
        logger.exception("metadata extraction error")
        metadata = None
    if not metadata:
        logger.error("unable to extract metadata", path)
        return None
    for line in metadata.exportPlaintext():
        if line.startswith('- Creation date: '):
            date_str = line[len('- Creation date: '):]
            return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    return None


def get_date(path):
    exif_date = get_exif_date(path)
    if exif_date:
        return (exif_date, "exif")
    meta_date = get_meta_data_date(path)
    if meta_date:
        return (meta_date, "meta")
    return (get_file_date(path), "file")


#-----------------
# Renaming
#-----------------

def rename(path, date):
    # dont trust OS file date for renaming
    if date[1] == "file":
        return None

    ctr = 0
    date_str = date[0].strftime("%Y%m%d_%H%M%S")

    renamed = "{}{}".format(date_str, os.path.splitext(path)[1])
    renamed_path = os.path.join(os.path.dirname(path), renamed)
    while path != renamed_path and os.path.isfile(renamed_path):
        ctr += 1
        renamed = "{}_{}{}".format(date_str, ctr, os.path.splitext(path)[1])
        renamed_path = os.path.join(os.path.dirname(path), renamed)

    if path != renamed_path:
        return renamed_path
    return None


def rename_all(folder):
    folder = os.path.abspath(folder)
    print("----------" + "-" * len(folder))
    print("Rename in {}".format(folder))
    print("----------"+ "-" * len(folder))

    print("Parsing files...")

    paths = []
    for path in os.listdir(folder):
        if os.path.isfile(os.path.join(folder, path)):
            paths.append(path)

    paths_dated = {}

    for path in paths:
        abs_path = os.path.join(folder, path)
        date = get_date(abs_path)
        renamed = rename(abs_path, date)
        if renamed:
            paths_dated[path] = date
            print("[{}] {} - {} -> {}".format(date[1], date[0].strftime("%Y/%m/%d %H:%M:%S"), path, renamed))
    
    print("Found {} files, {} to rename, execute ? (y/n)".format(len(paths), len(paths_dated)))
    if input("") != "y":
        return
    
    for path, date in paths_dated.items():
        abs_path = os.path.join(folder, path)
        renamed = rename(abs_path, date)
        if renamed:
            try:
                os.rename(abs_path, renamed)
                print(f"[renamed] {path} -> {renamed}")
            except Exception as e:
                logger.exception("rename failed")
                print(f"[failed] {path} -> {renamed}")


#-----------------
# Main
#-----------------

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) > 0:
        rename_all(args[0])
