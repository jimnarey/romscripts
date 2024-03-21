TITLES = [
    "Adventures of Batman and Robin, The (U) [p1][!].gen",
    "Advanced Daisenryaku (J) (REV01) [h1C].gen",
    "16 Tile Mahjong (1992)(City Man Technology - Gamtec)(TW)",
    "Addams Family Values (1994)(Ocean)(EU)(M3)",
    "Addams Family, The (1993)(Acclaim - Flying Edge)(EU-US)(en)",
    "Adventures of Rocky and Bullwinkle and Friends, The (1993)(Absolute Entertainment)(US)",
    "Asterix and the Great Rescue (Europe, Brazil) (En,Fr,De,Es,It).zip",
]

CODE_SPECS = [
    {
        "code": "[a#]",
        "code_type": "dump",
        "description": "The ROM is a copy of an alternative release of the game. "
        "Many games have been re-released to fix bugs or to eliminate "
        "Game Genie codes.",
        "regex": "\\[a[0-9]?\\]",
        "value": "Alternative",
    },
    {
        "code": "[h]",
        "code_type": "dump",
        "description": "The ROM has been user modified, with examples being changing "
        "the internal header or country codes, applying a release "
        "group intro, or editing the game's content.",
        "regex": "",
        "value": "Hacked",
    },
    {
        "code": "[b#]",
        "code_type": "dump",
        "description": "A ROM image which has been corrupted because the original "
        "game is very old, because of a faulty dumper (bad "
        "connection) or during its upload to a release server. These "
        "ROMs often have graphic errors or sometimes don't work at "
        "all.",
        "regex": "\\[b[0-9]?\\]",
        "value": "Bad",
    },
    {
        "code": "[p#]",
        "code_type": "dump",
        "description": "A dump of a pirated version of a game. These ROMs often have "
        "their copyright messages or company names removed or "
        'corrupted. Also, many ROMs contain "intro" screens with the '
        "name and symbols of the pirate group that have released "
        "them.",
        "regex": "\\[p[0-9]?\\]",
        "value": "Pirated",
    },
    {
        "code": "[!p]",
        "code_type": "dump",
        "description": "This is the closest dump to the original game to date, but "
        "the proper ROM is still waiting to be dumped.",
        "regex": "",
        "value": "Pending",
    },
    {
        "code": "[f#]",
        "code_type": "dump",
        "description": "A fixed dump is a ROM that has been altered to run better on " "a flashcart or an emulator.",
        "regex": "\\[f[0-9]?\\]",
        "value": "Fixed",
    },
    {
        "code": "[o#]",
        "code_type": "dump",
        "description": "The ROM contains more data than the original game. This "
        "extra data is useless and doesn't affect the game at all; it "
        "just makes the ROM bigger.",
        "regex": "\\[o[0-9]?\\]",
        "value": "Overdumped",
    },
    {
        "code": "[!]",
        "code_type": "dump",
        "description": "Verified - Good Dump. The ROM is an exact copy of the "
        "original game; it has not had any hacks or modifications.",
        "regex": "",
        "value": "verified",
    },
    {
        "code": "[t#]",
        "code_type": "dump",
        "description": "A trainer (special code which executes before starting the "
        "actual game) has been added to the ROM. It allows the player "
        "to access cheats from a menu or ingame.",
        "regex": "\\[t[0-9]?\\]",
        "value": "Trained",
    },
]
