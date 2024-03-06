# FBA XML Download

All available FBA XMLs are included in the repo. The following outlines the process for producing them.

The XML files for Final Burn Alpha are not available online, with the exception of the odd one here and there. None of the links for the executables on the FBA download page work. However, they can all be downloaded from [archive.org](https://web.archive.org/web/20210419143200/https://www.fbalpha.com/downloads/).

I tried automating this process, as with the MAME XMLs, but archive.org kept refusing connections using either Python's `urllib.request` module or the `requests` package. There aren't too many, so it was easier to download them using the browser.

The executable files come in `.7z` or `.zip` format, with the exception of one which is a (Windows) self-extracting executable. It can be extracted with WINE.

All versions except the earliest, 0.26 can be used to produce data files. This version can be discarded.

All files in `.7z` format can be extracted to separate directories with:

```
for file in *.7z; do 7z x -o"${file%.7z}" "$file"; done
```

All files in `.zip` format can be extracted to separate directories with:

```
find . -name '*.zip' -exec sh -c 'unzip -d "${1%.*}" "$1"' _ {} \;
```

Some of the directory names (like their source archives) include the substring `_unicode`. This can be removed in Python REPL with the following lines:

```
for dir in os.listdir():
    new_name = dir.replace("_unicode", "")
    os.rename(dir, new_name)
```

It may be necessary to remove the odd errant underscore from a small number of folder names to make them consistently named. Once this is done, an XML can be produced from each FBA executable with the `make_xmls.py` script. This will take a while. The FBA UI has to load for each run so there's a lot of clicking to get through each version.

Note that some of the earlier versions do not use XML but another format.
