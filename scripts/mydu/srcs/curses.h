#ifndef CURSES_H
# define CURSES_H
# include <ncurses.h>
# include "mydu.h"
# define WIN_NOBORDER		(1u << 0)
# define WIN_QUIT			(1u << 1)
# define WIN_NOQ			(1u << 2)
# define WIN_CONFIRM_CLOSE	(1u << 3)

# define BACKSPACE       	127

# define COLOR_DEFAULT		0
# define COLOR_SELECTED		1
# define COLOR_WINBORDERS	2

# define ARROW_UP      		65
# define ARROW_DOWN      	66
# define ARROW_RIGHT     	67
# define ARROW_LEFT     	68

/*
** node  : the current active node
** select : current selected node on the screen
** display_index: used to know wich entry we are actualy displaying (pagination purpose)
*/

struct main_window {
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
	int						(*draw)(struct curses_window *);
	int						(*input)(struct curses_window *, int);
	size_t					flags;
	void					*userdata;
};

int	 	 		curses_run(struct node *root, const struct config *cfg);
int             curses_confirm(struct curses_window *win,
    const char *message, const int initial);

void  			curses_box(int x, int y, int w, int h);
int             curses_new_window(struct curses_window *win);
void            curses_window_info(struct curses_window *win);
void            curses_window_decorate(struct curses_window *win);
void         	curses_refresh_parents(struct curses_window *win);
void            curses_puts_center(struct curses_window *win, const int line,
    const char *text, const size_t len);

int         	main_window_draw(struct curses_window *win);
int   			main_window_input(struct curses_window *win, int key);

void 	       	curses_files_run(struct curses_window *win, struct node *node);
size_t			curses_delete(struct curses_window *win, struct node *node);

#endif
