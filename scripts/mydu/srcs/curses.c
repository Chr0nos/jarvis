#include <stdlib.h>
#include "mydu.h"
#define COLOR_DEFAULT   0
#define COLOR_SELECTED  1
#define ALIGN_WSIZE     80
#define ALIGN_PC        90
#define ALIGN_FILES     102
#define ARROW_UP        65
#define ARROW_DOWN      66
#define BACKSPACE       127
#define OFFSET          10
// #define ARROW_RIGHT     67
// #define ARROW_LEFT      68

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

/*
** diff : number of lines under the display
*/

static enum e_iter_job   curses_display_iter(size_t level, struct node *node,
    void *userdata)
{
    struct curses_cfg       *cfg = userdata;
    char                    wsize[20];
    int                     pair;
    int                     diff;

    if ((level > 1) || ((node->space.total == 0) && (!(cfg->cfg->flags & FLAG_EMPTY_NODES))))
        return (STOP_NODE);
    cfg->display_index++;
    diff = (int)cfg->select_index - LINES;
    if ((int)cfg->display_index < diff + OFFSET)
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
        mvprintw(cfg->line++, 0, "--------------------\n");
    if (cfg->line > LINES)
        return (STOP_TREE);
    return (level == 0 ? CONTINUE : STOP_NODE);
}

static void         curses_init(const struct config *cfg,
    struct curses_cfg *cufg, struct node *root)
{
    *cufg = (struct curses_cfg) {
        .root = root,
        .node = root,
        .select = (root->childs) ? root->childs->content : root,
        .select_index = 0,
        .cfg = cfg,
        .should_quit = false
    };
}

static void         curses_select(struct curses_cfg *curse, int index)
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

static void         curses_updir(struct curses_cfg *curse)
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

static inline void  curses_error_key(const int key)
{
    clear();
    mvprintw(LINES >> 1, COLS >> 1, "unknow key: %c (%d)\n", (char)key, key);
    refresh();
    getch();
}

/*
** all user inputs are proceed here
*/

static void         curses_control(const int key, struct curses_cfg *curse)
{
    if ((char)key == 'q')
        curse->should_quit = true;
    else if ((char)key == '\n')
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
    }
    else if (key == BACKSPACE)
        curses_updir(curse);
    else if ((key == ARROW_DOWN) || (key == ARROW_UP))
        curses_select(curse,
            (int)curse->select_index + ((key == ARROW_UP) ? -1 : 1));
    else if (curse->cfg->flags & FLAG_VERBOSE)
        curses_error_key(key);
}

void                curses_debug(const struct curses_cfg *curse)
{
    mvprintw(0, 140, "%u\n", curse->select_index);
    mvprintw(1, 140, "%s\n", curse->node->path);
}

int                 curses_run(struct node *root, const struct config *cfg)
{
    struct curses_cfg   curse;

    curses_init(cfg, &curse, root);
    curse.win = initscr();
    if (!curse.win)
    {
        ft_dprintf(STDERR_FILENO, "%s", "Error: failed to create window.\n");
        return (EXIT_FAILURE);
    }
    start_color();
    init_pair(COLOR_DEFAULT, COLOR_WHITE, COLOR_GREEN);
    init_pair(COLOR_SELECTED, COLOR_CYAN, COLOR_BLACK);
    curs_set(0);
    while (!curse.should_quit)
    {
        clear();
        node_iter(PREFIX, curse.node, &curse, 0, &curses_display_iter);
        curse.line = 0;
        curse.display_index = 0;
        // curses_debug(&curse);
        refresh();
        curses_control(getch(), &curse);
    }
    endwin();
	node_iter(SUFFIX, root, NULL, 0, node_iter_clean);
    return (EXIT_SUCCESS);
}
