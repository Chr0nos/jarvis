#include "mydu.h"
#include <dirent.h>
#include <fcntl.h>
#include <sys/stat.h>

static int  curses_files_draw(struct curses_window *win, void *userdata)
{
    struct node     *node = userdata;
    DIR             *dir;
    struct dirent   *ent;
    struct stat     st;
    char            path[PATH_MAX];
    int             line = 2;

    if (!node)
        return (EXIT_FAILURE);
    dir = opendir(node->path);
    if (!dir)
        return (EXIT_FAILURE);
    while ((ent = readdir(dir)) != NULL)
    {
        ft_snprintf(path, PATH_MAX, "%s/%s", node->path, ent->d_name);
        if ((stat(path, &st) < 0) || (!(st.st_mode & S_IFREG)))
            continue ;
        mvprintw(win->y + line, win->x + 2, "%s", ent->d_name);
        mvprintw(win->y + line, win->x + win->w - 15, "%lu",
            (size_t)(st.st_blocks * BLK_SIZE));
        line++;
    }
    closedir(dir);
    return (EXIT_SUCCESS);
}

void        curses_files_run(struct curses_window *win, struct node *node)
{
    struct curses_window        files;
    char                        buf[FILENAME_MAXLEN];

    ft_snprintf(buf, FILENAME_MAXLEN, "%s%s", "Content of ", node->name);
    files = (struct curses_window) {
        .parent = win,
        .x = COLS / 4,
        .y = 5,
        .w = COLS >> 1,
        .h = LINES - 15,
        .title = buf,
        .draw = &curses_files_draw
    };
    curses_new_window(&files, node);
}
