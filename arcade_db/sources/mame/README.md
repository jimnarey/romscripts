# MAME DATs/XMLs

`download.py` downloads all available DAT/XML files from progetto snaps.

Some archives have both DAT and XML, some (approx 53 - 84, in rar format, just DAT).

BZIP  was used as it has the best compression ratio for text-based files. It's slow to compress but not much slower than other formats for decompression:

```
find . -maxdepth 1 -type f -name "*.xml" -exec bzip2 -k "{}" \;
```

Compressed, the collection of DAT/XML files is 1.6GB. Uncompressed it's 26.8GB.

When MAME and MESS became a single emulator (release 0.162  - May, 2015), the element name for romsets was changed. Prior to 0.162, individual arcade rom information/data was stored under "game". Starting with release 0.162 it is stored under "machine".

## cloneof and romof

The `sort_clones.py` script re-orders DAT files so parent romsets are declared before child romsets. This speeds up all database builds relying on those DAT files by eliminating what was, in earlier versions, a second loop through the DAT file.

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
    - A small number of romsets in the 29-37 DAT range are exceptions
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

- For each romset, get the `romof` and `cloneof` attributes.

- Extract the values for both parents:
    - Add the parents to a set of parents.
    - Add the romset to a set of children.


### Anomalous romsets

This is a copy of the summary of the `validate_sources.py` script as of MAME 0.262.

> The following displays in a table when viewed in a text editor.

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

### Sorting anomalous romsets

After running the sorting script, the following relationships are not resolved.

Validation errors: parent romsets found after children

Dat       	            Parent    	Index     	Child     	Index
MAME 0.35.xml.bz2	    btime     	1276      	btime2    	739
MAME 0.35.xml.bz2	    btime     	1276      	cookrace  	985

> The cause of these validation errors is that there are two `btime` romsets in the 0.35 DAT file. This will cause unpredictable behaviour when the database is built because it resolves `cloneof` and `romof` references by searching the database for games with the target name, compatible with the DAT's emulator version, then takes the first. In all other cases the first match is the only match. In this case, clone romsets could be linked to the wrong `btime`. However, it's too trivial a problem to write custom code to catch it, at least for now.

The sorting script (as of MAME 0.262) turns up some gaps in some of the DAT files:

Parent romsets not found

Dat       	            Element   	Parent
MAME 0.34rc2.xml.bz2	arknoidu  	arknoid
MAME 0.34rc1.xml.bz2	arknoidu  	arknoid
MAME 0.35b3.xml.bz2	    ldrun4    	ldrun2p
MAME 0.34b2.xml.bz2	    commandj  	commandoj
MAME 0.34b2.xml.bz2	    arknoidu  	arknoid
MAME 0.29.xml.bz2	    commandj  	commandoj
MAME 0.31.xml.bz2	    arknoidu  	arkanoidu
MAME 0.31.xml.bz2	    commandj  	commandoj
MAME 0.33b2.xml.bz2	    commandj  	commandoj
MAME 0.33b2.xml.bz2	    arknoidu  	arkanoidu
MAME 0.34b6.xml.bz2	    arknoidu  	arknoid
MAME 0.35b9.xml.bz2	    ldrun4    	ldrun2p
MAME 0.35b12.xml.bz2	ldrun4    	ldrun2p
MAME 0.37b7.dat.bz2	    pc_ynoid  	playch10
MAME 0.37b7.dat.bz2	    pc_wgnmn  	playch10
MAME 0.37b7.dat.bz2	    pc_wcup   	playch10
MAME 0.37b7.dat.bz2	    pc_vball  	playch10
MAME 0.37b7.dat.bz2	    pc_tmnt2  	playch10
MAME 0.37b7.dat.bz2	    pc_tmnt   	playch10
MAME 0.37b7.dat.bz2	    pc_tkfld  	playch10
MAME 0.37b7.dat.bz2	    pc_tenis  	playch10
MAME 0.37b7.dat.bz2	    pc_suprc  	playch10
MAME 0.37b7.dat.bz2	    pc_smb3   	playch10
MAME 0.37b7.dat.bz2	    pc_smb2   	playch10
MAME 0.37b7.dat.bz2	    pc_smb    	playch10
MAME 0.37b7.dat.bz2	    pc_rygar  	playch10
MAME 0.37b7.dat.bz2	    pc_rrngr  	playch10
MAME 0.37b7.dat.bz2	    pc_rnatk  	playch10
MAME 0.37b7.dat.bz2	    pc_rkats  	playch10
MAME 0.37b7.dat.bz2	    pc_rcpam  	playch10
MAME 0.37b7.dat.bz2	    pc_radrc  	playch10
MAME 0.37b7.dat.bz2	    pc_radr2  	playch10
MAME 0.37b7.dat.bz2	    pc_pwrst  	playch10
MAME 0.37b7.dat.bz2	    pc_pwbld  	playch10
MAME 0.37b7.dat.bz2	    pc_ngaid  	playch10
MAME 0.37b7.dat.bz2	    pc_ngai3  	playch10
MAME 0.37b7.dat.bz2	    pc_moglf  	playch10
MAME 0.37b7.dat.bz2	    pc_mman3  	playch10
MAME 0.37b7.dat.bz2	    pc_miket  	playch10
MAME 0.37b7.dat.bz2	    pc_kngfu  	playch10
MAME 0.37b7.dat.bz2	    pc_hgaly  	playch10
MAME 0.37b7.dat.bz2	    pc_grdus  	playch10
MAME 0.37b7.dat.bz2	    pc_goons  	playch10
MAME 0.37b7.dat.bz2	    pc_golf   	playch10
MAME 0.37b7.dat.bz2	    pc_gntlt  	playch10
MAME 0.37b7.dat.bz2	    pc_ftqst  	playch10
MAME 0.37b7.dat.bz2	    pc_ebike  	playch10
MAME 0.37b7.dat.bz2	    pc_duckh  	playch10
MAME 0.37b7.dat.bz2	    pc_drmro  	playch10
MAME 0.37b7.dat.bz2	    pc_ddrgn  	playch10
MAME 0.37b7.dat.bz2	    pc_dbldr  	playch10
MAME 0.37b7.dat.bz2	    pc_cvnia  	playch10
MAME 0.37b7.dat.bz2	    pc_cshwk  	playch10
MAME 0.37b7.dat.bz2	    pc_cntra  	playch10
MAME 0.37b7.dat.bz2	    pc_bfght  	playch10
MAME 0.37b7.dat.bz2	    pc_bball  	playch10
MAME 0.37b7.dat.bz2	    pc_1942   	playch10
MAME 0.37b6.dat.bz2	    pc_tkfld  	playch10
MAME 0.37b6.dat.bz2	    pc_smb3   	playch10
MAME 0.37b6.dat.bz2	    pc_smb    	playch10
MAME 0.37b6.dat.bz2	    pc_rnatk  	playch10
MAME 0.37b6.dat.bz2	    pc_pwrst  	playch10
MAME 0.37b6.dat.bz2	    pc_ngaid  	playch10
MAME 0.37b6.dat.bz2	    pc_miket  	playch10
MAME 0.37b6.dat.bz2	    pc_goons  	playch10
MAME 0.37b6.dat.bz2	    pc_ebike  	playch10
MAME 0.37b6.dat.bz2	    pc_duckh  	playch10
MAME 0.37b6.dat.bz2	    pc_ddrgn  	playch10
MAME 0.37b6.dat.bz2	    pc_cntra  	playch10
MAME 0.37b10.dat.bz2	superbik  	cvs
MAME 0.37b10.dat.bz2	hero      	cvs
MAME 0.37b10.dat.bz2	heartatk  	cvs
MAME 0.37b10.dat.bz2	huncholy  	cvs
MAME 0.37b10.dat.bz2	hunchbak  	cvs
MAME 0.37b10.dat.bz2	goldbug   	cvs
MAME 0.37b10.dat.bz2	dazzler   	cvs
MAME 0.37b10.dat.bz2	darkwar   	cvs
MAME 0.37b10.dat.bz2	cosmos    	cvs
MAME 0.37b10.dat.bz2	logger    	cvs
MAME 0.37b10.dat.bz2	pc_gntlt  	playch10
MAME 0.37b10.dat.bz2	pc_ftqst  	playch10
MAME 0.37b10.dat.bz2	pc_ebike  	playch10
MAME 0.37b10.dat.bz2	radarzon  	cvs
MAME 0.37b10.dat.bz2	pc_duckh  	playch10
MAME 0.37b10.dat.bz2	pc_drmro  	playch10
MAME 0.37b10.dat.bz2	pc_ddrgn  	playch10
MAME 0.37b10.dat.bz2	pc_dbldr  	playch10
MAME 0.37b10.dat.bz2	pc_cvnia  	playch10
MAME 0.37b10.dat.bz2	pc_cshwk  	playch10
MAME 0.37b10.dat.bz2	pc_cntra  	playch10
MAME 0.37b10.dat.bz2	pc_bstar  	playch10
MAME 0.37b10.dat.bz2	pc_bfght  	playch10
MAME 0.37b10.dat.bz2	pc_bball  	playch10
MAME 0.37b10.dat.bz2	pc_1942   	playch10
MAME 0.37b10.dat.bz2	wallst    	cvs
MAME 0.37b10.dat.bz2	8ball     	cvs
MAME 0.37b10.dat.bz2	pc_ynoid  	playch10
MAME 0.37b10.dat.bz2	pc_wgnmn  	playch10
MAME 0.37b10.dat.bz2	pc_wcup   	playch10
MAME 0.37b10.dat.bz2	pc_vball  	playch10
MAME 0.37b10.dat.bz2	pc_tmnt2  	playch10
MAME 0.37b10.dat.bz2	pc_tmnt   	playch10
MAME 0.37b10.dat.bz2	pc_tkfld  	playch10
MAME 0.37b10.dat.bz2	pc_suprc  	playch10
MAME 0.37b10.dat.bz2	pc_tenis  	playch10
MAME 0.37b10.dat.bz2	pc_smb3   	playch10
MAME 0.37b10.dat.bz2	pc_smb2   	playch10
MAME 0.37b10.dat.bz2	pc_smb    	playch10
MAME 0.37b10.dat.bz2	pc_rygar  	playch10
MAME 0.37b10.dat.bz2	pc_rrngr  	playch10
MAME 0.37b10.dat.bz2	pc_rnatk  	playch10
MAME 0.37b10.dat.bz2	pc_rkats  	playch10
MAME 0.37b10.dat.bz2	pc_rcpam  	playch10
MAME 0.37b10.dat.bz2	pc_radrc  	playch10
MAME 0.37b10.dat.bz2	pc_radr2  	playch10
MAME 0.37b10.dat.bz2	pc_pwrst  	playch10
MAME 0.37b10.dat.bz2	pc_pwbld  	playch10
MAME 0.37b10.dat.bz2	pc_ngaid  	playch10
MAME 0.37b10.dat.bz2	pc_ngai3  	playch10
MAME 0.37b10.dat.bz2	pc_mman3  	playch10
MAME 0.37b10.dat.bz2	pc_moglf  	playch10
MAME 0.37b10.dat.bz2	pc_miket  	playch10
MAME 0.37b10.dat.bz2	pc_kngfu  	playch10
MAME 0.37b10.dat.bz2	pc_hgaly  	playch10
MAME 0.37b10.dat.bz2	pc_grdus  	playch10
MAME 0.37b10.dat.bz2	pc_goons  	playch10
MAME 0.37b10.dat.bz2	pc_golf   	playch10
MAME 0.78.dat.bz2	    jdredd    	acpsx
MAME 0.78.dat.bz2	    brvblade  	psarc95
MAME 0.78.dat.bz2	    nbajamex  	acpsx
MAME 0.78.dat.bz2	    beastrzr  	psarc95
MAME 0.35b8.xml.bz2	    ldrun4    	ldrun2p
MAME 0.34b1.xml.bz2	    commandj  	commandoj
MAME 0.34b1.xml.bz2	    arknoidu  	arknoid
MAME 0.34b3.xml.bz2	    commandj  	commandoj
MAME 0.34b3.xml.bz2	    arknoidu  	arknoid
MAME 0.34b5.xml.bz2	    arknoidu  	arknoid
MAME 0.35b13.xml.bz2	ldrun4    	ldrun2p
MAME 0.35rc1.xml.bz2	ldrun4    	ldrun2p
MAME 0.35b6.xml.bz2	    ldrun4    	ldrun2p
MAME 0.36b12.xml.bz2	spacefbg  	spacefb.c
MAME 0.36b12.xml.bz2	spacedem  	spacefb.c
MAME 0.36b12.xml.bz2	spacebrd  	spacefb.c
MAME 0.36b12.xml.bz2	snowbroa  	snowbros.c
MAME 0.34b4.xml.bz2	    arknoidu  	arknoid
MAME 0.33b1.xml.bz2	    commandj  	commandoj
MAME 0.33b1.xml.bz2	    arknoidu  	arkanoidu
MAME 0.33b3.xml.bz2	    arknoidu  	arkanoidu
MAME 0.33b3.xml.bz2	    commandj  	commandoj
MAME 0.37b9.dat.bz2	    pc_ynoid  	playch10
MAME 0.37b9.dat.bz2	    pc_wgnmn  	playch10
MAME 0.37b9.dat.bz2	    pc_wcup   	playch10
MAME 0.37b9.dat.bz2	    pc_vball  	playch10
MAME 0.37b9.dat.bz2	    pc_tmnt2  	playch10
MAME 0.37b9.dat.bz2	    pc_tmnt   	playch10
MAME 0.37b9.dat.bz2	    pc_tkfld  	playch10
MAME 0.37b9.dat.bz2	    pc_tenis  	playch10
MAME 0.37b9.dat.bz2	    pc_suprc  	playch10
MAME 0.37b9.dat.bz2	    pc_smb3   	playch10
MAME 0.37b9.dat.bz2	    pc_smb2   	playch10
MAME 0.37b9.dat.bz2	    pc_smb    	playch10
MAME 0.37b9.dat.bz2	    pc_rygar  	playch10
MAME 0.37b9.dat.bz2	    pc_rrngr  	playch10
MAME 0.37b9.dat.bz2	    pc_rnatk  	playch10
MAME 0.37b9.dat.bz2	    pc_rkats  	playch10
MAME 0.37b9.dat.bz2	    pc_rcpam  	playch10
MAME 0.37b9.dat.bz2	    pc_radrc  	playch10
MAME 0.37b9.dat.bz2	    pc_radr2  	playch10
MAME 0.37b9.dat.bz2	    pc_pwrst  	playch10
MAME 0.37b9.dat.bz2	    pc_pwbld  	playch10
MAME 0.37b9.dat.bz2	    pc_ngaid  	playch10
MAME 0.37b9.dat.bz2	    pc_ngai3  	playch10
MAME 0.37b9.dat.bz2	    pc_moglf  	playch10
MAME 0.37b9.dat.bz2	    pc_mman3  	playch10
MAME 0.37b9.dat.bz2	    pc_miket  	playch10
MAME 0.37b9.dat.bz2	    pc_kngfu  	playch10
MAME 0.37b9.dat.bz2	    pc_hgaly  	playch10
MAME 0.37b9.dat.bz2	    pc_grdus  	playch10
MAME 0.37b9.dat.bz2	    pc_goons  	playch10
MAME 0.37b9.dat.bz2	    pc_golf   	playch10
MAME 0.37b9.dat.bz2	    pc_gntlt  	playch10
MAME 0.37b9.dat.bz2	    pc_ftqst  	playch10
MAME 0.37b9.dat.bz2	    pc_ebike  	playch10
MAME 0.37b9.dat.bz2	    pc_duckh  	playch10
MAME 0.37b9.dat.bz2	    pc_drmro  	playch10
MAME 0.37b9.dat.bz2	    pc_ddrgn  	playch10
MAME 0.37b9.dat.bz2	    pc_dbldr  	playch10
MAME 0.37b9.dat.bz2	    pc_cvnia  	playch10
MAME 0.37b9.dat.bz2	    pc_cshwk  	playch10
MAME 0.37b9.dat.bz2	    pc_cntra  	playch10
MAME 0.37b9.dat.bz2	    pc_bstar  	playch10
MAME 0.37b9.dat.bz2	    pc_bfght  	playch10
MAME 0.37b9.dat.bz2	    pc_bball  	playch10
MAME 0.37b9.dat.bz2	    pc_1942   	playch10
MAME 0.33rc1.xml.bz2	commandj  	commandoj
MAME 0.33rc1.xml.bz2	arknoidu  	arknoid
MAME 0.35b4.xml.bz2	    ldrun4    	ldrun2p
MAME 0.35b5.xml.bz2	    ldrun4    	ldrun2p
MAME 0.33b4.xml.bz2	    arknoidu  	arkanoidu
MAME 0.33b4.xml.bz2	    commandj  	commandoj
MAME 0.34b8.xml.bz2	    arknoidu  	arknoid
MAME 0.37b11.dat.bz2	superbik  	cvs
MAME 0.37b11.dat.bz2	radarzon  	cvs
MAME 0.37b11.dat.bz2	dazzler   	cvs
MAME 0.37b11.dat.bz2	darkwar   	cvs
MAME 0.37b11.dat.bz2	cosmos    	cvs
MAME 0.37b11.dat.bz2	wallst    	cvs
MAME 0.37b11.dat.bz2	pc_drmro  	playch10
MAME 0.37b11.dat.bz2	pc_ddrgn  	playch10
MAME 0.37b11.dat.bz2	pc_dbldr  	playch10
MAME 0.37b11.dat.bz2	pc_cvnia  	playch10
MAME 0.37b11.dat.bz2	pc_cshwk  	playch10
MAME 0.37b11.dat.bz2	pc_cntra  	playch10
MAME 0.37b11.dat.bz2	pc_bstar  	playch10
MAME 0.37b11.dat.bz2	pc_bfght  	playch10
MAME 0.37b11.dat.bz2	pc_bball  	playch10
MAME 0.37b11.dat.bz2	pc_1942   	playch10
MAME 0.37b11.dat.bz2	pc_duckh  	playch10
MAME 0.37b11.dat.bz2	pc_ynoid  	playch10
MAME 0.37b11.dat.bz2	pc_wgnmn  	playch10
MAME 0.37b11.dat.bz2	pc_wcup   	playch10
MAME 0.37b11.dat.bz2	pc_vball  	playch10
MAME 0.37b11.dat.bz2	pc_tmnt2  	playch10
MAME 0.37b11.dat.bz2	pc_tmnt   	playch10
MAME 0.37b11.dat.bz2	pc_tkfld  	playch10
MAME 0.37b11.dat.bz2	pc_tenis  	playch10
MAME 0.37b11.dat.bz2	pc_suprc  	playch10
MAME 0.37b11.dat.bz2	pc_smb3   	playch10
MAME 0.37b11.dat.bz2	pc_smb2   	playch10
MAME 0.37b11.dat.bz2	pc_smb    	playch10
MAME 0.37b11.dat.bz2	pc_rygar  	playch10
MAME 0.37b11.dat.bz2	pc_rrngr  	playch10
MAME 0.37b11.dat.bz2	pc_rnatk  	playch10
MAME 0.37b11.dat.bz2	pc_rkats  	playch10
MAME 0.37b11.dat.bz2	pc_rcpam  	playch10
MAME 0.37b11.dat.bz2	pc_radrc  	playch10
MAME 0.37b11.dat.bz2	pc_radr2  	playch10
MAME 0.37b11.dat.bz2	pc_pwrst  	playch10
MAME 0.37b11.dat.bz2	pc_pwbld  	playch10
MAME 0.37b11.dat.bz2	pc_ngaid  	playch10
MAME 0.37b11.dat.bz2	pc_ngai3  	playch10
MAME 0.37b11.dat.bz2	pc_moglf  	playch10
MAME 0.37b11.dat.bz2	pc_mman3  	playch10
MAME 0.37b11.dat.bz2	pc_miket  	playch10
MAME 0.37b11.dat.bz2	pc_kngfu  	playch10
MAME 0.37b11.dat.bz2	pc_hgaly  	playch10
MAME 0.37b11.dat.bz2	pc_grdus  	playch10
MAME 0.37b11.dat.bz2	pc_goons  	playch10
MAME 0.37b11.dat.bz2	pc_golf   	playch10
MAME 0.37b11.dat.bz2	pc_gntlt  	playch10
MAME 0.37b11.dat.bz2	pc_ftqst  	playch10
MAME 0.37b11.dat.bz2	pc_ebike  	playch10
MAME 0.37b11.dat.bz2	hero      	cvs
MAME 0.37b11.dat.bz2	heartatk  	cvs
MAME 0.37b11.dat.bz2	8ball     	cvs
MAME 0.37b11.dat.bz2	huncholy  	cvs
MAME 0.37b11.dat.bz2	hunchbak  	cvs
MAME 0.37b11.dat.bz2	logger    	cvs
MAME 0.37b11.dat.bz2	goldbug   	cvs
MAME 0.35b7.xml.bz2	    ldrun4    	ldrun2p
MAME 0.67.dat.bz2	    le2       	konamigx
MAME 0.67.dat.bz2	    tokkae    	konamigx
MAME 0.67.dat.bz2	    tbyahhoo  	konamigx
MAME 0.67.dat.bz2	    gokuparo  	konamigx
MAME 0.67.dat.bz2	    puzldama  	konamigx
MAME 0.67.dat.bz2	    sexyparo  	konamigx
MAME 0.67.dat.bz2	    daiskiss  	konamigx
MAME 0.33.xml.bz2	    commandj  	commandoj
MAME 0.33.xml.bz2	    arknoidu  	arknoid
MAME 0.34b7.xml.bz2	    arknoidu  	arknoid
MAME 0.33b7.xml.bz2	    arknoidu  	arknoid
MAME 0.33b7.xml.bz2	    commandj  	commandoj
MAME 0.33b6.xml.bz2	    arknoidu  	arkanoidu
MAME 0.33b6.xml.bz2	    commandj  	commandoj
MAME 0.35b10.xml.bz2	ldrun4    	ldrun2p
MAME 0.35b2.xml.bz2	    ldrun4    	ldrun2p
MAME 0.33b5.xml.bz2	    commandj  	commandoj
MAME 0.33b5.xml.bz2	    arknoidu  	arkanoidu
MAME 0.30.xml.bz2	    commandj  	commandoj
MAME 0.30.xml.bz2	    arknoidu  	arkanoidu
MAME 0.34.xml.bz2	    arknoidu  	arknoid
MAME 0.35b11.xml.bz2	ldrun4    	ldrun2p
MAME 0.37b8.dat.bz2	    pc_radrc  	playch10
MAME 0.37b8.dat.bz2	    pc_radr2  	playch10
MAME 0.37b8.dat.bz2	    pc_pwrst  	playch10
MAME 0.37b8.dat.bz2	    pc_pwbld  	playch10
MAME 0.37b8.dat.bz2	    pc_ngaid  	playch10
MAME 0.37b8.dat.bz2	    pc_ngai3  	playch10
MAME 0.37b8.dat.bz2	    pc_moglf  	playch10
MAME 0.37b8.dat.bz2	    pc_mman3  	playch10
MAME 0.37b8.dat.bz2	    pc_miket  	playch10
MAME 0.37b8.dat.bz2	    pc_kngfu  	playch10
MAME 0.37b8.dat.bz2	    pc_hgaly  	playch10
MAME 0.37b8.dat.bz2	    pc_grdus  	playch10
MAME 0.37b8.dat.bz2	    pc_goons  	playch10
MAME 0.37b8.dat.bz2	    pc_golf   	playch10
MAME 0.37b8.dat.bz2	    pc_gntlt  	playch10
MAME 0.37b8.dat.bz2	    pc_ftqst  	playch10
MAME 0.37b8.dat.bz2	    pc_ebike  	playch10
MAME 0.37b8.dat.bz2	    pc_duckh  	playch10
MAME 0.37b8.dat.bz2	    pc_drmro  	playch10
MAME 0.37b8.dat.bz2	    pc_ddrgn  	playch10
MAME 0.37b8.dat.bz2	    pc_dbldr  	playch10
MAME 0.37b8.dat.bz2	    pc_cvnia  	playch10
MAME 0.37b8.dat.bz2	    pc_cshwk  	playch10
MAME 0.37b8.dat.bz2	    pc_cntra  	playch10
MAME 0.37b8.dat.bz2	    pc_bfght  	playch10
MAME 0.37b8.dat.bz2	    pc_bball  	playch10
MAME 0.37b8.dat.bz2	    pc_1942   	playch10
MAME 0.37b8.dat.bz2	    pc_ynoid  	playch10
MAME 0.37b8.dat.bz2	    pc_wgnmn  	playch10
MAME 0.37b8.dat.bz2	    pc_wcup   	playch10
MAME 0.37b8.dat.bz2	    pc_vball  	playch10
MAME 0.37b8.dat.bz2	    pc_tmnt2  	playch10
MAME 0.37b8.dat.bz2	    pc_tmnt   	playch10
MAME 0.37b8.dat.bz2	    pc_tkfld  	playch10
MAME 0.37b8.dat.bz2	    pc_tenis  	playch10
MAME 0.37b8.dat.bz2	    pc_suprc  	playch10
MAME 0.37b8.dat.bz2	    pc_smb3   	playch10
MAME 0.37b8.dat.bz2	    pc_smb2   	playch10
MAME 0.37b8.dat.bz2	    pc_smb    	playch10
MAME 0.37b8.dat.bz2	    pc_rygar  	playch10
MAME 0.37b8.dat.bz2	    pc_rrngr  	playch10
MAME 0.37b8.dat.bz2	    pc_rnatk  	playch10
MAME 0.37b8.dat.bz2	    pc_rkats  	playch10
MAME 0.37b8.dat.bz2	    pc_rcpam  	playch10
