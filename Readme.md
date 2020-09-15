# pymage

Simple python script to rename all the media files in a folder according to their creation date.

To simplify ordering, rename files according to the following pattern `YYYYMMDD_HHMMSS` or `YYYYMMDD_HHMMSS_X` in case of conflict.

The creation date is searched in file meta-data.


# requirement

Require python installed with lib `hachoir` and `Pillow` installed listed in the `requirement.txt` file.

To install them with pip use `pip install -r .\requirement.txt`


# usage

`python .\pymage.py <dir>`

Example windows : `python .\pymage.py C:\Users\x\Pictures\Phone`

