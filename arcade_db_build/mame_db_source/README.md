# MAME DATs/XMLs

`download.py` downloads all available DAT/XML files from progetto snaps.

Some archives have both DAT and XML, some (approx 53 - 84, in rar format, just DAT).

BZIP  was used as it has the best compression ratio for text-based files. It's slow to compress but not much slower than other formats for decompression.

Compressed, the collection of DAT/XML files is 1.6GB. Uncompressed it's 26.8GB.

When MAME and MESS became a single emulator (release 0.162  - May, 2015), they changed how they store the data.  But only for what they call the rom file. I assume this was to create a better distinction between softlists (MESS) and arcade (MAME).

Prior to 0.162, individual arcade rom information/data was stored under "game".  Starting with release 0.162 they are stored under "machine".

So with 0.159, the Mame.xml would have its data listed under "game", and the importer is looking for "machine".
