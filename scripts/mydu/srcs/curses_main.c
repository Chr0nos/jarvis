#include <locale.h>
#include "mydu.h"
#define ALIGN_WSIZE     80
#define ALIGN_PC        90
#define ALIGN_FILES     102

/*
** diff : number of lines under the display
*/

static enum e_iter_job   curses_display_iter(size_t level, struct node *node,
    void *userdata)
{
    struct main_window      *cfg = userdata;
    char                    wsize[20];
    int                     pair;
    int                     diff;

    if ((level > 1) || ((node->space.total == 0) &&
            (!(cfg->cfg->flags & FLAG_EMPTY_NODES))))
        return (STOP_NODE);
    cfg->display_index++;
    diff = (int)cfg->select_index - LINES;
    if ((int)cfg->display_index < diff + (LINES >> 1))
        return CONTINUE;
    pair = COLOR_PAIR((cfg->select == node ? COLOR_SELECTED : COLOR_DEFAULT));
    attron(pair);
    ft_wsize(node->space.total, wsize, 20);
    mvprintw(cfg->line, ALIGN_WSIZE, "%s", wsize);
    mvprintw(cfg->line, ALIGN_PC, "%4.2f%%", (node->parent) ?
        (double)node->space.total / (double)node->parent->space.total * 100.0
        : 100);
    mvprintw(cfg->line, ALIGN_FILES, "%lu", node->files.total);
    mvprintw(cfg->line, 0, "%3d %s", cfg->display_index,
        (node == cfg->node) ? node->path : node->name);
    attroff(pair);
    cfg->line++;
    if (node == cfg->node)
		mvwhline(cfg->win->object, cfg->line++, 0, '-', 104);
    if (cfg->line > LINES)
        return (STOP_TREE);
    return (level == 0 ? CONTINUE : STOP_NODE);
}

/*
** search for "node" into lst, each lst->content is a (struct node *)
*/

static int            lst_indexof(struct s_list *lst, const struct node *node)
{
    int      i;

    i = 0;
    while (lst)
    {
        if (node == lst->content)
            return (i);
        i++;
        lst = lst->next;
    }
    return (-1);
}

static void         curses_select(struct main_window *curse, int index)
{
    struct s_list       *item;

    if (index < 0)
    {
        if (curse->node->parent)
        {
            curse->select = curse->node->parent;
            curse->select_index = 0;
            return ;
        }
        return ;
    }
    item = ft_lstat(curse->node->childs, index);
    if (!item)
        return ;
    curse->select = item->content;
    curse->select_index = (size_t)index;
}

/*
** move the current directory into the parent one.
** if no parent is available then does nothing
*/

static void         curses_updir(struct main_window *curse)
{
    int         idx;
    struct node *last;

    if (!curse->node->parent)
        return ;
    last = curse->node;
    curse->node = curse->node->parent;
    curse->select = last;
    idx = lst_indexof(curse->node->childs, last);
    if (idx >= 0)
        curse->select_index = (size_t)idx;
    else
        curse->select_index = 0;
}

static void main_window_refresh_fsi(struct main_window *curse)
{
    struct vfsinfo          *fsi = &curse->fs_info;

    *fsi = (struct vfsinfo) {
        .space_disk = curse->vfs_stats.f_bsize * curse->vfs_stats.f_blocks,
        .space_left = curse->vfs_stats.f_bsize * curse->vfs_stats.f_bfree,
    };
    fsi->space_used = fsi->space_disk - fsi->space_left;
}

int         main_window_draw(struct curses_window *win)
{
    struct main_window      *curse = win->userdata;

    main_window_refresh_fsi(curse);
    clear();
    node_iter(PREFIX, curse->node, curse, 0, &curses_display_iter);
    curse->line = 0;
    curse->display_index = 0;
    // mvprintw(LINES - 5, COLS - 10, "%lu", curse->fs_info.space_used);
    refresh();
    return (0);
}

static t_list	*lst_search_content(struct s_list *lst, const void *content)
{
	while (lst)
	{
		if (lst->content == content)
			return (lst);
		lst = lst->next;
	}
	return (NULL);
}

static void     main_window_delete(struct curses_window *win, struct node *node,
    struct main_window *curse)
{
    struct node     *parent;
    struct s_list   *lst;
    size_t          delta_size;
    size_t          delta_files;

    if (!node)
        return ;
    parent = node->parent;
    if ((!parent) || (!curses_delete(win, node)))
        return ;
    delta_size = node->space.total;
    delta_files = node->files.total;
	lst = lst_search_content(parent->childs, node);
	ft_lstremove(&lst, &parent->childs, NULL);
    if (curse->select_index > 0)
        curse->select_index--;
    lst = ft_lstat(parent->childs, (int)curse->select_index);
    curse->select = (!lst) ? NULL : lst->content;
    parent->space.total -= delta_size;
    parent->files.total -= delta_files;
}

int   main_window_input(struct curses_window *win, int key)
{
    struct main_window   *curse = win->userdata;

    if ((key == '\n') || (key == ARROW_RIGHT))
    {
        if (curse->select == curse->node)
            curses_updir(curse);
        else if (curse->select->files.total > 0)
        {
            curse->node = curse->select;
            curse->select_index = 0;
            curse->select = (curse->node->childs) ?
                curse->node->childs->content : curse->node;
        }
        statvfs(curse->node->path, &curse->vfs_stats);
    }
    else if ((key == BACKSPACE) || (key == ARROW_LEFT))
        curses_updir(curse);
    else if ((key == ARROW_DOWN) || (key == ARROW_UP))
        curses_select(curse,
            (int)curse->select_index + ((key == ARROW_UP) ? -1 : 1));
    else if (key == 'p')
        curses_window_info(win);
    else if (key == 'f')
        curses_files_run(win, curse->node);
    else if (key == 'd')
        main_window_delete(win, curse->select, curse);
    return (0);
}

int     main_window_init(struct curses_window *win)
{
    struct main_window  *curse = win->userdata;

    setlocale(LC_ALL, "");
    start_color();
	noecho();
	init_pair(COLOR_DEFAULT, COLOR_WHITE, COLOR_GREEN);
    init_pair(COLOR_SELECTED, COLOR_CYAN, COLOR_BLACK);
	init_pair(COLOR_WINBORDERS, COLOR_MAGENTA, COLOR_BLACK);
	curs_set(0);
    main_window_refresh_fsi(curse);
    statvfs(curse->node->path, &curse->vfs_stats);
    return (0);
}
