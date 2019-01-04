#include "mydu.h"
#define CONFIRM_DECO    "+----------------------------------+"
#define CONFIRM_BORDER  '|'
#define CONFIRM_DECOLEN 36
#define MARGIN          15

/*
** just draw an empty rectangle on the screen
** if "x" or "y" is negative then the center of the screen will be choosed
*/

static inline void  curses_confirm_empty(int x, int y, int w, int h)
{
    int     line;

    if (x < 0)
        x = (LINES >> 1) - (h >> 1);
    if (y < 0)
        y = (COLS >> 1) - (w >> 1);
    line = x + h;
    mvprintw(x, y, "%s", CONFIRM_DECO);
    mvprintw(line, y, "%s", CONFIRM_DECO);
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

/*
** Prompt a confirmation window then return the use choice,
** if the user quit before selecting a value the intial value will be returned
*/

int                curses_confirm(const char *message, const int initial)
{
    const size_t    len = ft_strlen(message);
    int             ret = initial;
    int             line_center;
    int             key = 0;

    line_center = (int)LINES >> 1;
    do
    {
        curses_confirm_empty(-1, -1, CONFIRM_DECOLEN, 6);
        mvprintw(line_center - 1, (COLS >> 1) - (int)(len >> 1), "%s", message);
        curses_confirm_button(
            line_center + 1,
            ((COLS >> 1) - (CONFIRM_DECOLEN >> 1)) + MARGIN,
            "Yes", ret);
        curses_confirm_button(
            line_center + 1,
            ((COLS >> 1) + (CONFIRM_DECOLEN >> 1)) - MARGIN,
            "No", !ret);
        refresh();
        key = getch();
        if (key == 'q')
            return (initial);
        if ((key == ARROW_LEFT) || (key == ARROW_RIGHT))
            ret = !ret;
    }
    while (key != '\n');
    return (ret);
}
