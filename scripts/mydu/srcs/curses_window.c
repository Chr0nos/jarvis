#include "mydu.h"

void               curses_puts_center(struct curses_window *win, const int line,
    const char *text, const size_t len)
{
    mvprintw(
        win->x + line,
        win->y + 1 + (win->w / 2) - ((int)len / 2),
        "%s",
        text);
}

int                curses_new_window(struct curses_window *win, void *userdata)
{
    int             ret;
    int             key;
    const size_t    title_len = (win->title) ? ft_strlen(win->title) : 0;

    do
    {
        if (!(win->flags & WIN_NOBORDER))
            curses_box(win->x, win->y, win->w, win->h);
        if (win->title)
            curses_puts_center(win, 1, win->title, title_len);
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
        if ((win->flags & WIN_CONFIRM_CLOSE) && (key == 'q') &&
                (!curses_confirm("Quit ?", false)))
            key = 0;
    }
    while ((key != 'q') || (win->flags & WIN_NOQ));
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
