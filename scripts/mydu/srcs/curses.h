#ifndef CURSES_H
# define CURSES_H
# include <ncurses.h>
# include "mydu.h"

/*
** node  : the current active node
** select : current selected node on the screen
** display_index: used to know wich entry we are actualy displaying (pagination purpose)
*/

struct curses_cfg {
	const struct config	    *cfg;
	struct node		        *root;
	struct node		        *node;
	struct node		        *select;
	size_t			        select_index;
	WINDOW                  *win;
	int				        line;
	int				        should_quit;
	size_t			        display_index;
};

struct curses_window {
	struct cursed_window	*parent;
	const char				*title;
	int						x;
	int						y;
	int						w;
	int						h;
	size_t					flags;
	struct curses_cfg		*curse;
};

int	 	 		curses_run(struct node *root, const struct config *cfg);
void         	curses_debug(const struct curses_cfg *curse);
int             curses_confirm(const char *message, const int initial);
void  			curses_box(int x, int y, int w, int h);
int             curses_new_window(
    struct curses_window *win,
    void *userdata,
    int (*draw)(struct curses_window *, void *),
    int (*input)(struct curses_window *, void *, int));

#endif
