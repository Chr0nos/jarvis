#include "mydu.h"

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