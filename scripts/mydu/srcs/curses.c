#include <stdlib.h>
#include "mydu.h"
#define COLOR_DEFAULT   0
#define COLOR_SELECTED  1
#define ALIGN_WSIZE     100
#define ALIGN_FILES     122
#define ARROW_UP        65
#define ARROW_DOWN      66
#define BACKSPACE       127
#define ESCAPE          27
// #define ARROW_RIGHT     67
// #define ARROW_LEFT      68

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

static enum e_iter_job   curses_display_iter(size_t level, struct node *node,
    void *userdata)
{
    struct curses_cfg       *cfg = userdata;
    char                    wsize[20];
    int                     pair;

    pair = COLOR_PAIR((cfg->select == node ? COLOR_SELECTED : COLOR_DEFAULT));
    attron(pair);
    ft_wsize(node->space.total, wsize, 20);
    mvprintw(cfg->line, 0, "%s\n",
        (node == cfg->node) ? node->path : node->name);
    mvprintw(cfg->line, ALIGN_WSIZE, "%s", wsize);
    mvprintw(cfg->line, ALIGN_FILES, "%lu", node->files.total);
    attroff(pair);
    cfg->line++;
    if (node == cfg->node)
        mvprintw(cfg->line++, 0, "--------------------\n");
    if (cfg->line > LINES)
        return (STOP_TREE);
    return (level == 0 ? CONTINUE : STOP_NODE);
}

static void     curses_init(const struct config *cfg, struct curses_cfg *cufg,
    struct node *root)
{
    *cufg = (struct curses_cfg) {
        .root = root,
        .node = root,
        .select = root,
        .cfg = cfg,
        .should_quit = false
    };
}

static void     curse_select(struct curses_cfg *curse, int index)
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

static void     curses_updir(struct curses_cfg *curse)
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

static void     curses_control(const int key, struct curses_cfg *curse)
{
    if (((char)key == 'q') || (key == ESCAPE))
        curse->should_quit = true;
    else if ((char)key == '\n')
    {
        curse->node = curse->select;
        curse->select_index = 0;
    }
    else if (key == BACKSPACE)
        curses_updir(curse);
    else if ((key == ARROW_DOWN) || (key == ARROW_UP))
        curse_select(curse,
            (int)curse->select_index + ((key == ARROW_UP) ? -1 : 1));
    else //if (curse->cfg->flags & FLAG_VERBOSE)
    {
        clear();
        mvprintw(LINES >> 1, COLS >> 1, "unknow key: %c (%d)\n", (char)key, key);
        refresh();
        getch();
    }
}

int             curses_run(struct node *root, const struct config *cfg)
{
    struct curses_cfg   curse;

    curses_init(cfg, &curse, root);
    curse.win = initscr();
    if (!curse.win)
        return (EXIT_FAILURE);
    start_color();
    init_pair(COLOR_DEFAULT, COLOR_WHITE, COLOR_GREEN);
    init_pair(COLOR_SELECTED, COLOR_CYAN, COLOR_BLACK);
    while (!curse.should_quit)
    {
        clear();
        node_iter(PREFIX, curse.node, &curse, 0, &curses_display_iter);
        curse.line = 0;
        refresh();
        curses_control(getch(), &curse);
    }
    endwin();
	node_iter(SUFFIX, root, NULL, 0, node_iter_clean);
    return (EXIT_SUCCESS);
}
