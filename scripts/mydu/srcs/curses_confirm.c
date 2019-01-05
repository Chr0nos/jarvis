#include "mydu.h"
#define CORNER_TOP_LEFT     'A'
#define CORNER_TOP_RIGHT    'B'
#define CORNER_BOT_LEFT     'C'
#define CORNER_BOT_RIGHT    'D'
#define CONFIRM_BORDER      '|'
#define CONFIRM_WIDTH       36
#define CONFIRM_HEIGHT      6
#define MARGIN              7

/*
** just draw an empty rectangle on the screen
** if "x" or "y" is negative then the center of the screen will be choosed
*/

void  curses_box(int x, int y, int w, int h)
{
    int     line;
    int     col;

    if (x < 0)
        x = (LINES >> 1) - (h >> 1);
    if (y < 0)
        y = (COLS >> 1) - (w >> 1);
    line = x + h;
    col = y + w - 2;
    mvprintw(x, y, "%c", CORNER_TOP_LEFT);
    mvprintw(x, col + 1, "%c", CORNER_TOP_RIGHT);
    mvprintw(line, y, "%c", CORNER_BOT_LEFT);
    mvprintw(line, col + 1, "%c", CORNER_BOT_RIGHT);
    while (col > y)
    {
        mvprintw(x, col, "-");
        mvprintw(line, col, "-");
        col--;
    }
    line--;
    while (line > x)
    {
        mvprintw(line, y, "%c%-*s%c", CONFIRM_BORDER, w - 2, "", CONFIRM_BORDER);
        line--;
    }
}

static void         curses_confirm_button(const int x, const int y,
    const char *button, const bool selected)
{
    int             pair;

    pair = COLOR_PAIR((selected == false) ? COLOR_DEFAULT : COLOR_SELECTED);
    attron(pair);
    mvprintw(x, y, "%s", button);
    attroff(pair);
}

static int          curses_confirm_input(struct curses_window *win,
    void *userdata, int key)
{
    int         *ret = userdata;

    if ((key == ARROW_LEFT) || (key == ARROW_RIGHT))
        *ret = !*ret;
    else if (key == '\n')
    {
        win->flags |= WIN_QUIT;
        return (*ret);
    }
    return (EXIT_SUCCESS);
}

static int          curses_confirm_draw(struct curses_window *win,
    void *userdata)
{
    const int ret = *((int *)userdata);
    const int line = LINES >> 1;
    const int col = win->y + (win->w >> 1);

    curses_confirm_button(line, col - MARGIN, "Yes", ret);
    curses_confirm_button(line, col + MARGIN, "No", !ret);
    return (EXIT_SUCCESS);
}

/*
** Prompt a confirmation window then return the use choice,
** if the user quit before selecting a value the intial value will be returned
*/

__attribute((pure))
int                 curses_confirm(struct curses_window *win,
    const char *message, const int initial)
{
    struct curses_window    this;
    int                     ret = initial;

    this = (struct curses_window) {
        .parent = win,
        .x = win->x + (win->h >> 1) - (CONFIRM_HEIGHT >> 1),
        .y = win->y + (win->w >> 1) - (CONFIRM_WIDTH >> 1),
        .w = CONFIRM_WIDTH,
        .h = CONFIRM_HEIGHT,
        .title = message,
        .input = &curses_confirm_input,
        .draw = &curses_confirm_draw
    };
    return (curses_new_window(&this, &ret));
}
