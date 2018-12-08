# About this tool
This is my tool to replace the unix program "du" because I found it dumb:
the real du displays directories in order of walk through the filesystem but
who wants that ?

The user just needs to see "where is my disk space ?! Which is the folder pumping it
all ?"

That's what "mydu" does: it displays the content of a folder sorted by size,
taking care of the content of children directories

# Options
Option          | Purpose
----------------|:-----------------------
| -c            | displays in csv format (to use with > file.csv )
| -e            | displays empty nodes anyway
| -r            | reverses the display
| -l            | local stats only (does not take children in the stats)
| -p            | displays the full path, not only the current node name
| --max-level=x | x is the max amount of sub-directories to DISPLAY (not to scan), x must be a positive or 0

# Build it
Just type "make" and make sure to have "git" and "clang" installed