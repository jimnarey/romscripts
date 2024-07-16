To do:

Immediate:
- Use lxml in place of built-in library
- Replace all list comprehensions with .findall()
- Create rom index based on hash of name, size, md5
- Create game indexes. Consider one based on name, roms and disk(s)
- Time each DAT and get an average time per game
- Count the number of games in the validation script so we can calculate a total build time
- Log any unhandled references
- Consider logging any invalid references (circular)
- Add FBA parsing
- Add FBN DATs and parsing
- Enable updating an existing database with new DATs

Later:
 - Decide what to do when existing instances have additional attributes in later DATs. E.g. 'bios' in Rom.
 - Decide whether to add the 'bios' field to Rom. Work out what the 'biosset' elements are really for.
 - What about fields which could plausibly change between DATs? (How sure are we that e.g. 'sourcefile' in Game doesn't change?) cloneof and romof are fine in the current implementation. To ensure coherent responses to queries we just need to filter by emulator, but the database structure is sound.
