#include "mydu.h"
#include <dirent.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <stdlib.h>

static int  curses_files_cmp(struct s_list *a, struct s_list *b)
{
    const struct file_entry *fa = a->content;
    const struct file_entry *fb = b->content;

    if (fa->st.st_blocks < fb->st.st_blocks)
        return (1);
    else if (fa->st.st_blocks > fb->st.st_blocks)
        return (-1);
    return (ft_strcmp(fa->name, fb->name));
}

static int  curses_files_draw(struct curses_window *win)
{
    int                 line;
    struct s_list       *lst;
    struct file_entry   *file;

    line = 3;
    lst = ((struct files_window *)win->userdata)->content;
    while (lst)
    {
        file = lst->content;
        lst = lst->next;
        if (file->st.st_mode & S_IFDIR)
            continue ;
        mvprintw(win->y + line, win->x + 2, "%s%s", file->name,
            (file->st.st_mode & S_IFDIR) ? "/" : "");
        mvprintw(win->y + line, win->x + win->w - 8, "%s", file->wsize);
        line++;
    }
    return (EXIT_SUCCESS);
}

static struct file_entry *curses_files_mkentry(const char *path, const char *name)
{
    struct file_entry   *entry;

    entry = ft_memalloc(sizeof(struct file_entry));
    if (!entry)
        return (NULL);
    ft_strcpy(entry->name, name);
    if (stat(path, &entry->st) >= 0)
        ft_wsize(WSIZE_LEN, entry->wsize, (size_t)(entry->st.st_blocks * BLK_SIZE));
    else
        ft_strcpy(entry->wsize, "???");
    return (entry);
}

static int  curses_files_init(struct curses_window *win)
{
    struct files_window         *files = win->userdata;
	DIR				            *dir;
	struct dirent               *ent;
    struct file_entry           *entry;
    char                        path[PATH_MAX];

    files->content = NULL;
    dir = opendir(files->node->path);
    if (!dir)
    {
        // TODO : display error window here
        win->flags |= WIN_QUIT;
        return (-1);
    }
    statfs(files->node->path, &files->fs);
    while ((ent = (readdir(dir))) != NULL)
    {
        ft_snprintf(path, PATH_MAX, "%s/%s", files->node->path, ent->d_name);
        entry = curses_files_mkentry(path, ent->d_name);
        if (entry)
            ft_lstpush_sort(&files->content,
                ft_lstnewlink(entry, 0), &curses_files_cmp);
    }
    closedir(dir);
    return (0);
}

static int  curses_files_quit(struct curses_window *win)
{
    struct files_window     *files = win->userdata;

    ft_lstdel(&files->content, &ft_lstpulverisator);
    return (0);
}

void        curses_files_run(struct curses_window *win, struct node *node)
{
    struct curses_window        this;
    struct files_window         files;

    files.node = node;
    ft_snprintf(files.title, PATH_MAX, "%s%s", "Content of ", node->name);
    this = (struct curses_window) {
        .parent = win,
        .x = COLS / 4,
        .y = 5,
        .w = COLS >> 1,
        .h = LINES - 15,
        .title = files.title,
        .draw = &curses_files_draw,
        .init = &curses_files_init,
        .quit = &curses_files_quit,
        .userdata = &files
    };
    curses_new_window(&this);
}
