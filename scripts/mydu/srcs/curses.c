#include <ncurses.h>
#include <stdlib.h>
#include "mydu.h"

static void     curses_display(struct node *parent, const struct config *cfg)
{
    struct s_list   *lst;
    struct node     *node;
    int             line;

    (void)cfg;
    lst = parent->childs;
    line = 0;
    while (lst)
    {
        node = lst->content;
        mvprintw(line, 0, "|- %c %s\n",
            node->files.total > 0 ? '+' : '-',
            node->path);
        line++;
        lst = lst->next;
    }
}

int             curses_run(struct node *root, const struct config *cfg)
{
    WINDOW          *win;
    struct node     *node;
    bool            should_quit;
    int             key;

    node = root;
    win = initscr();
    if (!win)
        return (EXIT_FAILURE);
    should_quit = false;
    key = 0;
    while (!should_quit)
    {
        clear();
        curses_display(root, cfg);
        refresh();
        key = getch();
        if ((char)key == 'q')
            should_quit = true;
    }
    endwin();
    puts("quit");
    return (EXIT_SUCCESS);
}
