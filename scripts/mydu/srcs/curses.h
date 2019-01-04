#ifndef CURSES_H
# define CURSES_H
# include <ncurses.h>
# include "mydu.h"
# define WIN_NOBORDER		(1u << 0)
# define WIN_QUIT			(1u << 1)

# define BACKSPACE       	127

# define COLOR_DEFAULT		0
# define COLOR_SELECTED		1

# define ARROW_UP      		65
# define ARROW_DOWN      	66
# define ARROW_RIGHT     	67
# define ARROW_LEFT     	68

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
	int						padding;
	size_t			        display_index;
};

struct curses_window {
	struct curses_window	*parent;
	const char				*title;
	int						x;
	int						y;
	int						w;
	int						h;
	int						(*draw)(struct curses_window *, void *);
	int						(*input)(struct curses_window *, void *, int);
	size_t					flags;
	struct curses_cfg		*curse;
};

int	 	 		curses_run(struct node *root, const struct config *cfg);
int             curses_confirm(const char *message, const int initial);
void  			curses_box(int x, int y, int w, int h);
int             curses_new_window(struct curses_window *win, void *userdata);
void            curses_window_info(struct curses_window *win);

int         	main_window_draw(struct curses_window *win, void *userdata);
int   			main_window_input(struct curses_window *win, void *userdata, int key);

#endif
