#include "mydu.h"

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
    mvprintw(line++, col, "flags: %#lx", win->parent->flags);
	wrefresh(win->object);
	return (0);
}

void                curses_window_info(struct curses_window *win)
{
    struct curses_window    info;
    char                    *title;

    ft_asprintf(&title, "%s '%s'", "Information about", win->title);
    info = (struct curses_window){
        .parent = win,
        .x = (int)((win->x == 0) ? 10 : win->x + 3),
        .y = (int)((win->y == 0) ? 3 : win->y + 3),
        .w = 80,
        .h = 10,
        .title = title,
		.draw = curses_window_info_draw
	};
    curses_new_window(&info);
    if (title)
        free(title);
}
