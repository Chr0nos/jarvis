#include "mydu.h"

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

void         curses_refresh_parents(struct curses_window *win)
{
    if (!win)
        return ;
    if (win->draw)
        win->draw(win, NULL);
    if (win->parent)
        curses_refresh_parents(win->parent);
}

static int          curses_window_info_input(struct curses_window *win,
    void *userdata, int key)
{
    (void)userdata;
    if (key == 'p')
    {
        curses_window_info(win);
        curses_refresh_parents(win);
    }
    return (0);
}

void                curses_window_info(struct curses_window *win)
{
    struct curses_window    info;

    info = (struct curses_window){
        .parent = win,
        .x = (int)(win->h * 0.25f),
        .y = (int)(win->w * 0.25f),
        .w = 80,
        .h = 10,
        .title = "Window information",
        .curse = win->curse,
        .input = curses_window_info_input
    };
    curses_new_window(&info, NULL);
}
