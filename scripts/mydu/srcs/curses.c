#include <stdlib.h>
#include "mydu.h"

static void         curses_init(const struct config *cfg,
    struct main_window *cufg, struct node *root)
{
    *cufg = (struct main_window) {
        .root = root,
        .node = root,
        .select = (root->childs) ? root->childs->content : root,
        .select_index = 0,
        .cfg = cfg,
    };
}

int                 curses_run(struct node *root, const struct config *cfg)
{
    struct curses_window    main;
    struct main_window      curse;

    curses_init(cfg, &curse, root);
    main.object = initscr();
    if (!main.object)
    {
        ft_dprintf(STDERR_FILENO, "%s", "Error: failed to create window.\n");
        return (EXIT_FAILURE);
    }
	curse.win = &main;
    main = (struct curses_window) {
        .w = COLS,
        .h = LINES,
        .flags = WIN_NOBORDER | WIN_CONFIRM_CLOSE,
        .title = "Mydu Main",
        .init = &main_window_init,
        .draw = &main_window_draw,
        .input = &main_window_input,
        .userdata = &curse,
		.object = main.object
    };
    curses_new_window(&main);
    endwin();
	node_iter(SUFFIX, root, NULL, 0, node_iter_clean);
    return (EXIT_SUCCESS);
}
