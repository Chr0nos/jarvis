#include "mydu.h"

/*
** put a string in the center of a window at the specified "line"
** len : the string lenght to put
*/

void                curses_puts_center(
    struct curses_window *win,
    const int line,
    const char *text,
    const size_t len)
{
    mvprintw(
        win->y + line,
        win->x + 1 + (win->w / 2) - ((int)len / 2),
        "%.*s",
        len,
        text);
}

void                curses_window_decorate(struct curses_window *win)
{
    if (!(win->flags & WIN_NOBORDER))
        curses_box(win->x, win->y, win->w, win->h);
    if (win->title)
        curses_puts_center(win, 1, win->title, ft_strlen(win->title));
}

/*
** This is a main loop for window system, util the window is not exited this
** function will not return.
** to close the window the caller has to set a flag WIN_QUIT then the loop
** will return the same data as the user specified.
** to return pointers add a field in your structure provided by userdata
*/

int                 curses_new_window(struct curses_window *win)
{
    int             ret;
    int             key;

	if (!win->object)
		win->object = newwin(win->h, win->w, win->y, win->x);
    do
    {
        curses_window_decorate(win);
        if (win->draw)
        {
            ret = win->draw(win);
            if (win->flags & WIN_QUIT)
                return (ret);
        }
        else
            refresh();
        move(LINES - 1, COLS - 1);
        key = getch();
        if (win->input)
        {
            ret = win->input(win, key);
            if (win->flags & WIN_QUIT)
                return (ret);
        }
        if ((win->flags & WIN_CONFIRM_CLOSE) && (key == 'q') &&
                (!curses_confirm(win, "Quit ?", false)))
            key = 0;
    }
    while ((key != 'q') || (win->flags & WIN_NOQ));
	delwin(win->object);
    return (0);
}

void         curses_refresh_parents(struct curses_window *win)
{
    if (!win)
        return ;
    if (win->parent)
        curses_refresh_parents(win->parent);
    curses_window_decorate(win);
    if (win->draw)
        win->draw(win);
}

static int          curses_window_info_input(struct curses_window *win, int key)
{
    if (key == 'p')
    {
        curses_window_info(win);
        curses_refresh_parents(win);
    }
    if (key == 'r')
        win->title = "renamed !";
    return (0);
}

static int			curses_window_info_draw(struct curses_window *win)
{
	const int 	col = win->x + (win->w >> 1) - 4;
	int			line;

	if (!win->parent)
		return (-1);
	line = win->y + 3;
	mvprintw(line++, col, "x: %2d", win->parent->x);
	mvprintw(line++, col, "y: %2d", win->parent->y);
	mvprintw(line++, col, "w: %2d", win->parent->w);
	mvprintw(line++, col, "h: %2d", win->parent->h);
	mvprintw(line++, col, "u: %p", win->parent->userdata);
	wrefresh(win->object);
	return (0);
}

void                curses_window_info(struct curses_window *win)
{
    struct curses_window    info;

    info = (struct curses_window){
        .parent = win,
        .x = (int)((win->x == 0) ? 10 : win->x + 3),
        .y = (int)((win->y == 0) ? 3 : win->y + 3),
        .w = 80,
        .h = 10,
        .title = "Window information",
        .input = curses_window_info_input,
		.draw = curses_window_info_draw
	};
    curses_new_window(&info);
}
