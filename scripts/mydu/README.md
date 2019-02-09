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
| -i            | interactive mode (ncurses)
| -f            | display files too (be carefull of memory consumtion !)
| -a            | wakk into hiddens directories (be carefull with .git dirs...)
| --max-level=x | x is the max amount of sub-directories to DISPLAY (not to scan), x must be a positive or 0

# Interactive mode
You can use the up/down arrow to select the target to go, then press enter, use backspace to go to the parent directory.
Press "q" to quit.

## Keys
Key                 | Purpose
--------------------|:-----------------------------------------
| f                 | open the current directory files list
| d                 | delete the selected directory
| p                 | open infomations about the current window (in progress...)
| q                 | close the current window
| t                 | toggle the global disk space stats
| up/down arrows    | move in the list of a window
| left/right arrows | in the main window, enter/exit selection, used in selection to change the choice
| enter             | validate a choice or enter a directory
| backspace         | go to the parent directory

# Symlinks
This tool does not show symlinks because the main purpose is to find heavy objects 
on the disk quickly, there is no benefit to to walk over symlinks in this context.

# Build it
Just type "make" and make sure to have "git", "clang" and "ncurses" installed

# Supported operating systems
i develop this tool on an Arch Linux 64 bits unstable and mac os high sierra
- Linux
- MacOs
- Probably all bsd like

# Contribute
If you wan to contribute it will be a pleasure for me, feel free to open issues and ask
for new things

# Debug curses mode ?
Because the curses mode use stdout/stderr it may be difficult to debug it.
The solution is to run mydu in gdbserver and connect to it from an other terminal.

### On terminal 1
```
make CFLAGS="-g3" re
gdbserver gdbserver 127.0.0.1:2345 ./mydu -i
```

### On terminal 2
```
gdb
target remote 127.0.0.1:2345
c
```
