#include "mydu.h"

// static void curses_puts(struct curses_window *win, int x, int y, const char *format, ...)
// {
//     mvprintw(win->y + y, win->x + x, format, &format[8]);
// }

static  int curses_fileinfo_draw(struct curses_window *win)
{
    const struct file_entry     *file = win->userdata;
    int                         line = 3;

    mvprintw(win->y + line, win->x + 2, "%s %lu",
        "inode:", file->st.st_ino);
    // curses_puts(win, 5, 5, "%s %d", "hello world", 42);
    mvprintw(win->y + line++, win->x + 2, "%-10s %s", "name:", file->name);
    mvprintw(win->y + line++, win->x + 2, "%-10s %03o", "perms:", file->st.st_mode & 0x777);
    return (0);
}

void        curses_filefinfo(struct curses_window *win, struct file_entry *file)
{
    struct curses_window        this;

    this = (struct curses_window) {
        .parent = win,
        .title = "File infomations",
        .draw = &curses_fileinfo_draw,
        .userdata = file
    };
    curses_new_window(curses_centerfrom_parent(&this, 40, 20));
}
