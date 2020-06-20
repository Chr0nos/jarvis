# Bwarg
This is a mass file renamed wrote in python, it allow the user to rename files using regex and pattern matching

The UI uses PyQt5


# Regex formats
Python3 regex

# Replace format
You can take a look here: https://pyformat.info/

can can either use `{}` (positional matching) or `{named}` (named matching)
for the named matching your capture group muse have:
```
(?P<name>.+)
```

to name "anything" on the key `name`

## Common replacements
### Prefix files
put `replace` to : `(.+)` wich mean "match on everything" and then in `by` set `Myprefix {}`

### Series episodes notation
In this case you want to match on things like `S04E45`, to do so the regex is: `.+(S\d+E\d+).+` but you also want the extenssion of the file, then `.+(S\d+E\d+).+\.(\w+)`

and renamed by: `Serie's name {}.{}`

# What happen if two files will have the same renaming?
In this case only the first one will be renamed, the others will keep the old name
