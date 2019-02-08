#include "mydu.h"

static  int curses_fileinfo_draw(struct curses_window *win)
{
    const struct file_entry     *file = win->userdata;
    int                         line = 3;
    // char                        path[PATH_MAX];

    mvprintw(win->y + line, win->x + 2, "%s %lu", "inode:", file->st.st_ino);
    // mvprintw(win->y + line++, win->x + 2, "%-10s %s", "name:", file->name);
    mvprintw(win->y + line++, win->x + 2, "%-10s %03o", "perms:", file->st.st_mode & 0777);
    mvprintw(win->y + line++, win->x + 2, "%-10s %d", "uid:", file->st.st_uid);
    mvprintw(win->y + line++, win->x + 2, "%-10s %d", "gid:", file->st.st_gid);
    mvprintw(win->y + line++, win->x + 2, "%-10s %lu", "size:", file->st.st_size);
#ifndef linux
    mvprintw(win->y + line++, win->x + 2, "%-10s %lu", "atime:", file->st.st_atimespec.tv_nsec);
    mvprintw(win->y + line++, win->x + 2, "%-10s %lu", "mtime:", file->st.st_mtimespec.tv_nsec);
    mvprintw(win->y + line++, win->x + 2, "%-10s %lu", "ctime:", file->st.st_ctimespec.tv_nsec);
#endif
    // node_path(((struct files_window *)win->parent->userdata)->node, path, PATH_MAX);
    // mvprintw(win->y + line++, win->x + 2, "%-10s %s", "path", path);
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
