#include <stdlib.h>
#include "mydu.h"

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

void                curses_debug(const struct curses_cfg *curse)
{
    mvprintw(0, 140, "%u\n", curse->select_index);
    mvprintw(1, 140, "%s\n", curse->node->path);
}

int                curses_new_window(struct curses_window *win, void *userdata)
{
    int             ret;
    int             key;

    do
    {
        if (!(win->flags & WIN_NOBORDER))
            curses_box(win->x, win->y, win->w, win->h);
        if (win->title)
            mvprintw(win->x + 1, win->y + 2, "%s", win->title);
        if (win->draw)
        {
            ret = win->draw(win, userdata);
            if (ret)
                return (ret);
            if (win->flags & WIN_QUIT)
                return (0);
        }
        else
            refresh();
        key = getch();
        if (win->input)
            win->input(win, userdata, key);
    }
    while (key != 'q');
    return (0);
}

int                 curses_run(struct node *root, const struct config *cfg)
{
    struct curses_window    main;
    struct curses_cfg       curse;

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
    main = (struct curses_window) {
        .w = COLS,
        .h = LINES,
        .flags = WIN_NOBORDER,
        .curse = &curse,
        .draw = &main_window_draw,
        .input = &main_window_input
    };
    curses_new_window(&main, NULL);
    endwin();
	node_iter(SUFFIX, root, NULL, 0, node_iter_clean);
    return (EXIT_SUCCESS);
}
