# MAME DATs/XMLs

`download.py` downloads all available DAT/XML files from progetto snaps.

Some archives have both DAT and XML, some (approx 53 - 84, in rar format, just DAT).

BZIP  was used as it has the best compression ratio for text-based files. It's slow to compress but not much slower than other formats for decompression.

Compressed, the collection of DAT/XML files is 1.6GB. Uncompressed it's 26.8GB.

When MAME and MESS became a single emulator (release 0.162  - May, 2015), they changed how they store the data.  But only for what they call the rom file. I assume this was to create a better distinction between softlists (MESS) and arcade (MAME).

Prior to 0.162, individual arcade rom information/data was stored under "game".  Starting with release 0.162 they are stored under "machine".

So with 0.159, the Mame.xml would have its data listed under "game", and the importer is looking for "machine".

## cloneof and romof

The `sort_clones.py` script re-orders DAT files so, as far as possible, parent romsets are declared before child romsets. This speeds up all database builds relying on those DAT files by significantly reducing the number of elements iterated in the second loop (possibly to zero).

The relationships can be as follows. A romset may:

- Be a `romof` parent and have no parents of either type.
    - This would generally be a bios or other shared romset, e.g. `neogeo` or `naomi`.

- Be a `romof` parent and also be a `romof` child.
    - E.g. some NeoGeo clones are a `romof` (and `cloneof`) of another NeoGeo romset which is itself a `romof` of `neogeo`.

- Be a `cloneof` parent and be a `romof` child.

- Be a `cloneof` parent a **OR** a `cloneof` child but not both.

- Have neither a `romof` nor `cloneof` attribute.

- Have just a `romof` attribute and no `cloneof`.

- **Very rarely** have a `cloneof` attribute and no `romof` attribute.
    - A small numver of romsets in the 29-37 DAT range are exceptions
    - We can largely disregard these because in most cases where a romset has both types of parent, the values are the same, so we adopt the same logic. We do need to explicitly check for this though.

- **Almost never** be a `romof` parent and a `cloneof` child.
    - The only exception is in a handful of DAT files in the 31-33 range, where `karnovj` is a `romof` parent to `chelnovj` and a `cloneof` child of `karnov`.

- Refer to itself in its `romof` attribute. These can be ignored for sorting purposes (but we need to explicity check for these).

- Refer to the same parent in its `romof` and `cloneof` attributes.
    - This is the case for the vast majority of romsets which have a `cloneof` attribute.

- Refer to different parents in its `romof` and `cloneof` attributes.
    - As of MAME 262 there are 85 cases of this spread across the full collection of DAT files

### Summary

From these rules/convetions, we can derive the following:

- `romof` chains are never more than three romsets in length (this is also explicitly tested for in validate_sources.py)
- `cloneof` chains are never more than two romsets in length
- chains combining both attributes are never more than three roms long, with the possible exceptions of some involving the 85 roms which have a `cloneof` attribute and a `romof` attribute with a different value

There are the folowing categories of romssets:
1. Has no parent, has `romof` children.
2. Has a `romof` parent and no children.
3. Has a `romof` parent and no `cloneof` parent. Has children (don't need to worry about which attribute, but will usually be both).
4. Has a parent set on both `romof` and `cloneof` attributes.
5. Has different parents set on the `romof` and `cloneof` attributes.
6. Has no parents or children.

Rather than worry about the individual hierarchies, which is slow to process, we can ensure that parents are declared before children in the DAT file by identifying the groups above and sorting them in the order: 1, 3, 4, 5, everything else.

### Sorting logic

The rules/conventions above lead to the following sorting rules:

- Loop through the game/machine elements, creating a dictionary using the romset name as a key.

- For each romset, get the `romof` and `cloneof` attributes:
    - Extract a single value if both parents are the same:
        - Add the parent to a set of parents.
        - Add the romset to a set of children.
    - Extract a single value if there is only a `romof` or (rarely) just a `cloneof` attribute.
        - Add the parent to a set of parents.
        - Add the romset to a set of children.
    - Extract both values if `romof` and `cloneof` are different.
        - Add both parents to a set of parents.
        - Add the romset to a set of romsets with multiple parents

- Compare the sets:
    - Romsets which are parents but have no parents are added to an 'apex' set.


### Anomalous romsets

This is a copy of the summary of the `validate_sources.py` script as of MAME 0.262.

85 romsets with different cloneof and romof attributes

Dat       	            Name      	Romof     	Cloneof
MAME 0.34rc2.xml.bz2	arknoidu  	arknoid   	arkanoid
MAME 0.34rc1.xml.bz2	arknoidu  	arknoid   	arkanoid
MAME 0.35b3.xml.bz2	    ldrun4    	ldrun2p   	ldrun
MAME 0.35b3.xml.bz2 	maglordh  	neogeo    	maglord
MAME 0.35b3.xml.bz2	    puzzldpr  	neogeo    	puzzledp
MAME 0.34b2.xml.bz2	    arknoidu  	arknoid   	arkanoid
MAME 0.34b2.xml.bz2	    commandj  	commandoj 	commando
MAME 0.29.xml.bz2	    commandj  	commandoj 	commando
MAME 0.31.xml.bz2	    arknoidu  	arkanoidu 	arkanoid
MAME 0.31.xml.bz2	    chelnovj  	karnovj   	karnov
MAME 0.31.xml.bz2	    commandj  	commandoj 	commando
MAME 0.33b2.xml.bz2	    arknoidu  	arkanoidu 	arkanoid
MAME 0.33b2.xml.bz2	    chelnovj  	karnovj   	karnov
MAME 0.33b2.xml.bz2	    commandj  	commandoj 	commando
MAME 0.34b6.xml.bz2	    arknoidu  	arknoid   	arkanoid
MAME 0.35b9.xml.bz2	    ldrun4    	ldrun2p   	ldrun
MAME 0.35b9.xml.bz2	    maglordh  	neogeo    	maglord
MAME 0.35b9.xml.bz2	    puzzldpr  	neogeo    	puzzledp
MAME 0.35b12.xml.bz2	ldrun4    	ldrun2p   	ldrun
MAME 0.35b12.xml.bz2	maglordh  	neogeo    	maglord
MAME 0.35b12.xml.bz2	puzzldpr  	neogeo    	puzzledp
MAME 0.35b8.xml.bz2	    ldrun4    	ldrun2p   	ldrun
MAME 0.35b8.xml.bz2	    maglordh  	neogeo    	maglord
MAME 0.35b8.xml.bz2	    puzzldpr  	neogeo    	puzzledp
MAME 0.34b1.xml.bz2	    arknoidu  	arknoid   	arkanoid
MAME 0.34b1.xml.bz2	    commandj  	commandoj 	commando
MAME 0.34b3.xml.bz2	    arknoidu  	arknoid   	arkanoid
MAME 0.34b3.xml.bz2	    commandj  	commandoj 	commando
MAME 0.34b5.xml.bz2	    arknoidu  	arknoid   	arkanoid
MAME 0.35b13.xml.bz2	ldrun4    	ldrun2p   	ldrun
MAME 0.35b13.xml.bz2	maglordh  	neogeo    	maglord
MAME 0.35rc1.xml.bz2	ldrun4    	ldrun2p   	ldrun
MAME 0.35b6.xml.bz2	    ldrun4    	ldrun2p   	ldrun
MAME 0.35b6.xml.bz2	    maglordh  	neogeo    	maglord
MAME 0.35b6.xml.bz2	    puzzldpr  	neogeo    	puzzledp
MAME 0.36b12.xml.bz2	silvland  	rpatrolb  	cclimber
MAME 0.36b12.xml.bz2	snowbroa  	snowbros  	snowbros.c
MAME 0.36b12.xml.bz2	spacebrd  	spacefb   	spacefb.c
MAME 0.36b12.xml.bz2	spacedem  	spacefb   	spacefb.c
MAME 0.36b12.xml.bz2	spacefbg  	spacefb   	spacefb.c
MAME 0.34b4.xml.bz2	    arknoidu  	arknoid   	arkanoid
MAME 0.33b1.xml.bz2	    arknoidu  	arkanoidu 	arkanoid
MAME 0.33b1.xml.bz2	    chelnovj  	karnovj   	karnov
MAME 0.33b1.xml.bz2	    commandj  	commandoj 	commando
MAME 0.33b3.xml.bz2	    arknoidu  	arkanoidu 	arkanoid
MAME 0.33b3.xml.bz2	    chelnovj  	karnovj   	karnov
MAME 0.33b3.xml.bz2	    commandj  	commandoj 	commando
MAME 0.33rc1.xml.bz2	arknoidu  	arknoid   	arkanoid
MAME 0.33rc1.xml.bz2	commandj  	commandoj 	commando
MAME 0.35b4.xml.bz2	    ldrun4    	ldrun2p   	ldrun
MAME 0.35b4.xml.bz2	    maglordh  	neogeo    	maglord
MAME 0.35b4.xml.bz2	    puzzldpr  	neogeo    	puzzledp
MAME 0.35b5.xml.bz2	    ldrun4    	ldrun2p   	ldrun
MAME 0.35b5.xml.bz2	    maglordh  	neogeo    	maglord
MAME 0.35b5.xml.bz2	    puzzldpr  	neogeo    	puzzledp
MAME 0.33b4.xml.bz2	    arknoidu  	arkanoidu 	arkanoid
MAME 0.33b4.xml.bz2	    chelnovj  	karnovj   	karnov
MAME 0.33b4.xml.bz2	    commandj  	commandoj 	commando
MAME 0.34b8.xml.bz2	    arknoidu  	arknoid   	arkanoid
MAME 0.35b7.xml.bz2	    ldrun4    	ldrun2p   	ldrun
MAME 0.35b7.xml.bz2	    maglordh  	neogeo    	maglord
MAME 0.35b7.xml.bz2	    puzzldpr  	neogeo    	puzzledp
MAME 0.33.xml.bz2	    arknoidu  	arknoid   	arkanoid
MAME 0.33.xml.bz2	    commandj  	commandoj 	commando
MAME 0.34b7.xml.bz2	    arknoidu  	arknoid   	arkanoid
MAME 0.33b7.xml.bz2	    arknoidu  	arknoid   	arkanoid
MAME 0.33b7.xml.bz2	    commandj  	commandoj 	commando
MAME 0.33b6.xml.bz2	    arknoidu  	arkanoidu 	arkanoid
MAME 0.33b6.xml.bz2	    chelnovj  	karnovj   	karnov
MAME 0.33b6.xml.bz2	    commandj  	commandoj 	commando
MAME 0.35b10.xml.bz2	ldrun4    	ldrun2p   	ldrun
MAME 0.35b10.xml.bz2	maglordh  	neogeo    	maglord
MAME 0.35b10.xml.bz2	puzzldpr  	neogeo    	puzzledp
MAME 0.35b2.xml.bz2	    ldrun4    	ldrun2p   	ldrun
MAME 0.35b2.xml.bz2	    maglordh  	neogeo    	maglord
MAME 0.35b2.xml.bz2	    puzzldpr  	neogeo    	puzzledp
MAME 0.33b5.xml.bz2	    arknoidu  	arkanoidu 	arkanoid
MAME 0.33b5.xml.bz2	    chelnovj  	karnovj   	karnov
MAME 0.33b5.xml.bz2	    commandj  	commandoj 	commando
MAME 0.30.xml.bz2	    arknoidu  	arkanoidu 	arkanoid
MAME 0.30.xml.bz2	    commandj  	commandoj 	commando
MAME 0.34.xml.bz2	    arknoidu  	arknoid   	arkanoid
MAME 0.35b11.xml.bz2	ldrun4    	ldrun2p   	ldrun
MAME 0.35b11.xml.bz2	maglordh  	neogeo    	maglord
MAME 0.35b11.xml.bz2	puzzldpr  	neogeo    	puzzledp

135 romsets with cloneof but no romof

Dat       	            Name      	Cloneof
MAME 0.36b6.xml.bz2	    midresu   	midres
MAME 0.34rc2.xml.bz2	pacmanbl  	pacman
MAME 0.34rc2.xml.bz2	spaceph   	invaders
MAME 0.36.xml.bz2	    midresu   	midres
MAME 0.34rc1.xml.bz2	pacmanbl  	pacman
MAME 0.34rc1.xml.bz2	spaceph   	invaders
MAME 0.35b3.xml.bz2	    pacmanbl  	pacman
MAME 0.35b3.xml.bz2	    si_sv     	invaders
MAME 0.35b3.xml.bz2	    spaceph   	invaders
MAME 0.36b2.xml.bz2	    midresu   	midres
MAME 0.34b2.xml.bz2	    pacmanbl  	pacman
MAME 0.34b2.xml.bz2	    spaceph   	invaders
MAME 0.36b11.xml.bz2	midresu   	midres
MAME 0.29.xml.bz2	    dkjrbl    	dkongjr
MAME 0.29.xml.bz2	    dkjrjp    	dkongjr
MAME 0.29.xml.bz2	    pacmanbl  	pacman
MAME 0.37b1.xml.bz2	    midresu   	midres
MAME 0.36b8.xml.bz2	    midresu   	midres
MAME 0.31.xml.bz2	    dkjrbl    	dkongjr
MAME 0.31.xml.bz2	    dkjrjp    	dkongjr
MAME 0.31.xml.bz2	    joustg    	joust
MAME 0.31.xml.bz2	    pacmanbl  	pacman
MAME 0.31.xml.bz2	    spaceph   	invaders
MAME 0.33b2.xml.bz2	    dkjrbl    	dkongjr
MAME 0.33b2.xml.bz2	    dkjrjp    	dkongjr
MAME 0.33b2.xml.bz2	    joustg    	joust
MAME 0.33b2.xml.bz2	    pacmanbl  	pacman
MAME 0.33b2.xml.bz2	    spaceph   	invaders
MAME 0.36b9.1.xml.bz2	midresu   	midres
MAME 0.34b6.xml.bz2	    pacmanbl  	pacman
MAME 0.34b6.xml.bz2	    spaceph   	invaders
MAME 0.35rc2.xml.bz2	ckongalc  	ckong
MAME 0.35rc2.xml.bz2	pacmanbl  	pacman
MAME 0.35b9.xml.bz2	    pacmanbl  	pacman
MAME 0.35b9.xml.bz2	    si_sv     	invaders
MAME 0.35b9.xml.bz2	    spaceph   	invaders
MAME 0.35b12.xml.bz2	pacmanbl  	pacman
MAME 0.35b12.xml.bz2	si_sv     	invaders
MAME 0.36b14.xml.bz2	midresu   	midres
MAME 0.35b8.xml.bz2	    pacmanbl  	pacman
MAME 0.35b8.xml.bz2	    si_sv     	invaders
MAME 0.35b8.xml.bz2	    spaceph   	invaders
MAME 0.34b1.xml.bz2	    pacmanbl  	pacman
MAME 0.34b1.xml.bz2	    spaceph   	invaders
MAME 0.36b3.xml.bz2	    midresu   	midres
MAME 0.36b7.xml.bz2	    midresu   	midres
MAME 0.34b3.xml.bz2	    pacmanbl  	pacman
MAME 0.34b3.xml.bz2	    spaceph   	invaders
MAME 0.35fix.xml.bz2	midresu   	midres
MAME 0.34b5.xml.bz2	    pacmanbl  	pacman
MAME 0.34b5.xml.bz2	    spaceph   	invaders
MAME 0.35b13.xml.bz2	pacmanbl  	pacman
MAME 0.35rc1.xml.bz2	ckongalc  	ckong
MAME 0.35rc1.xml.bz2	pacmanbl  	pacman
MAME 0.36rc2.xml.bz2	midresu   	midres
MAME 0.35b6.xml.bz2	    pacmanbl  	pacman
MAME 0.35b6.xml.bz2	    si_sv     	invaders
MAME 0.35b6.xml.bz2	    spaceph   	invaders
MAME 0.36b12.xml.bz2	midresu   	midres
MAME 0.34b4.xml.bz2	    pacmanbl  	pacman
MAME 0.34b4.xml.bz2	    spaceph   	invaders
MAME 0.33b1.xml.bz2	    dkjrbl    	dkongjr
MAME 0.33b1.xml.bz2	    dkjrjp    	dkongjr
MAME 0.33b1.xml.bz2	    joustg    	joust
MAME 0.33b1.xml.bz2	    pacmanbl  	pacman
MAME 0.33b1.xml.bz2	    spaceph   	invaders
MAME 0.37b2.xml.bz2	    midresu   	midres
MAME 0.33b3.xml.bz2	    dkjrbl    	dkongjr
MAME 0.33b3.xml.bz2	    dkjrjp    	dkongjr
MAME 0.33b3.xml.bz2	    joustg    	joust
MAME 0.33b3.xml.bz2	    pacmanbl  	pacman
MAME 0.33b3.xml.bz2	    spaceph   	invaders
MAME 0.33rc1.xml.bz2	pacmanbl  	pacman
MAME 0.33rc1.xml.bz2	spaceph   	invaders
MAME 0.35b4.xml.bz2	    pacmanbl  	pacman
MAME 0.35b4.xml.bz2	    si_sv     	invaders
MAME 0.35b4.xml.bz2	    spaceph   	invaders
MAME 0.36b13.xml.bz2	midresu   	midres
MAME 0.36b5.xml.bz2	    midresu   	midres
MAME 0.35b5.xml.bz2	    pacmanbl  	pacman
MAME 0.35b5.xml.bz2	    si_sv     	invaders
MAME 0.35b5.xml.bz2	    spaceph   	invaders
MAME 0.33b4.xml.bz2	    dkjrbl    	dkongjr
MAME 0.33b4.xml.bz2	    dkjrjp    	dkongjr
MAME 0.33b4.xml.bz2	    joustg    	joust
MAME 0.33b4.xml.bz2	    pacmanbl  	pacman
MAME 0.33b4.xml.bz2	    spaceph   	invaders
MAME 0.35b1.xml.bz2	    pacmanbl  	pacman
MAME 0.35b1.xml.bz2	    spaceph   	invaders
MAME 0.34b8.xml.bz2	    pacmanbl  	pacman
MAME 0.34b8.xml.bz2	    spaceph   	invaders
MAME 0.35b7.xml.bz2	    pacmanbl  	pacman
MAME 0.35b7.xml.bz2	    si_sv     	invaders
MAME 0.35b7.xml.bz2	    spaceph   	invaders
MAME 0.35.xml.bz2	    ckongalc  	ckong
MAME 0.35.xml.bz2	    midresu   	midres
MAME 0.35.xml.bz2	    pacmanbl  	pacman
MAME 0.33.xml.bz2	    pacmanbl  	pacman
MAME 0.33.xml.bz2	    spaceph   	invaders
MAME 0.36b15.xml.bz2	midresu   	midres
MAME 0.36b4.xml.bz2	    midresu   	midres
MAME 0.36b1.xml.bz2	    midresu   	midres
MAME 0.34b7.xml.bz2	    pacmanbl  	pacman
MAME 0.34b7.xml.bz2	    spaceph   	invaders
MAME 0.33b7.xml.bz2	    pacmanbl  	pacman
MAME 0.33b7.xml.bz2	    spaceph   	invaders
MAME 0.33b6.xml.bz2	    dkjrbl    	dkongjr
MAME 0.33b6.xml.bz2	    dkjrjp    	dkongjr
MAME 0.33b6.xml.bz2	    joustg    	joust
MAME 0.33b6.xml.bz2	    pacmanbl  	pacman
MAME 0.33b6.xml.bz2	    spaceph   	invaders
MAME 0.36b10.xml.bz2	midresu   	midres
MAME 0.35b10.xml.bz2	pacmanbl  	pacman
MAME 0.35b10.xml.bz2	si_sv     	invaders
MAME 0.35b10.xml.bz2	spaceph   	invaders
MAME 0.36b16.xml.bz2	midresu   	midres
MAME 0.35b2.xml.bz2	    pacmanbl  	pacman
MAME 0.35b2.xml.bz2	    spaceph   	invaders
MAME 0.36rc1.xml.bz2	midresu   	midres
MAME 0.33b5.xml.bz2	    dkjrbl    	dkongjr
MAME 0.33b5.xml.bz2	    dkjrjp    	dkongjr
MAME 0.33b5.xml.bz2	    joustg    	joust
MAME 0.33b5.xml.bz2	    pacmanbl  	pacman
MAME 0.33b5.xml.bz2	    spaceph   	invaders
MAME 0.30.xml.bz2	    dkjrbl    	dkongjr
MAME 0.30.xml.bz2	    dkjrjp    	dkongjr
MAME 0.30.xml.bz2	    joustg    	joust
MAME 0.30.xml.bz2	    pacmanbl  	pacman
MAME 0.30.xml.bz2	    spaceph   	invaders
MAME 0.34.xml.bz2	    pacmanbl  	pacman
MAME 0.34.xml.bz2	    spaceph   	invaders
MAME 0.35b11.xml.bz2	pacmanbl  	pacman
MAME 0.35b11.xml.bz2	si_sv     	invaders
MAME 0.35b11.xml.bz2	spaceph   	invaders
MAME 0.36b9.0.xml.bz2	midresu   	midres
