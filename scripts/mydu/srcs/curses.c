#include <stdlib.h>
#include "mydu.h"
#define COLOR_DEFAULT   0
#define COLOR_SELECTED  1
#define ALIGN_WSIZE     100
#define ALIGN_FILES     122
#define ARROW_UP        65
#define ARROW_DOWN      66
// #define ARROW_RIGHT     67
// #define ARROW_LEFT      68

static enum e_iter_job   curses_display_iter(size_t level, struct node *node,
    void *userdata)
{
    struct curses_cfg       *cfg = userdata;
    char                    wsize[20];
    int                     pair;

    pair = COLOR_PAIR((cfg->select == node ? COLOR_SELECTED : COLOR_DEFAULT));
    attron(pair);
    ft_wsize(node->space.total, wsize, 20);
    mvprintw(cfg->line, 0, "%s\n", node->name);
    mvprintw(cfg->line, ALIGN_WSIZE, "%s", wsize);
    mvprintw(cfg->line, ALIGN_FILES, "%lu", node->files.total);
    attroff(pair);
    cfg->line++;
    // if (node == cfg->root)
    //     mvprintw(cfg->line++, 0, "--------------------\n");
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
        if (curse->select->parent)
        {
            curse->select = curse->select->parent;
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

static void     curses_control(const int key, struct curses_cfg *curse)
{
    if ((char)key == 'q')
        curse->should_quit = true;
    else if ((char)key == '\n')
        curse->node = curse->select;
    else if (key == 127)
    {
        if (!curse->node->parent)
            return ;
        curse->node = curse->node->parent;
        curse->select = curse->node->parent;
        curse->select_index = 0;
    }
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
    puts("quit");
	node_iter(SUFFIX, root, NULL, 0, node_iter_clean);
    return (EXIT_SUCCESS);
}
