#ifndef CURSES_H
# define CURSES_H
# include <ncurses.h>
# include <sys/param.h>
# include <sys/mount.h>
# ifdef linux
#  include <sys/statfs.h>
# endif
# include "mydu.h"
# define WIN_NOBORDER		(1u << 0)
# define WIN_QUIT			(1u << 1)
# define WIN_NOQ			(1u << 2)
# define WIN_CONFIRM_CLOSE	(1u << 3)
# define WIN_NOINPUT		(1u << 4)

# define WSIZE_LEN			16

# define BACKSPACE       	127

# define COLOR_DEFAULT		0
# define COLOR_SELECTED		1
# define COLOR_WINBORDERS	2

# define ARROW_UP      		65
# define ARROW_DOWN      	66
# define ARROW_RIGHT     	67
# define ARROW_LEFT     	68

struct curses_window;

struct fsinfo {
	size_t					space_disk;
	size_t					space_left;
	size_t					space_used;
};


/*
** node  : the current active node
** select : current selected node on the screen
** display_index: used to know wich entry we are actualy displaying (pagination purpose)
*/

# define MWF_TOTALPC		(1u)

struct main_window {
	const struct config	    *cfg;
	struct node		        *root;
	struct node		        *node;
	struct node		        *select;
	size_t			        select_index;
	int				        line;
	unsigned int			flags;
	size_t			        display_index;
	struct statfs			fs_stats;
	struct fsinfo			fs_info;
	struct curses_window	*win;
};

struct file_entry {
	char					name[FILENAME_MAX];
	char					wsize[WSIZE_LEN];
	struct stat				st;
};

struct files_window {
	WINDOW					*pad;
	struct node				*node;
	struct s_list			*content;
	struct statfs			fs;
	char					title[PATH_MAX];
};

struct deletion_task {
	struct node				*node;
	size_t					deleted_items;
};

struct curses_window {
	struct curses_window	*parent;
	const char				*title;
	int						x;
	int						y;
	int						w;
	int						h;
	int						(*init)(struct curses_window *);
	int						(*draw)(struct curses_window *);
	int						(*input)(struct curses_window *, int);
	int						(*quit)(struct curses_window *);
	size_t					flags;
	WINDOW					*object;
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
    const char *text, size_t len);

int				main_window_init(struct curses_window *win);
int         	main_window_draw(struct curses_window *win);
int   			main_window_input(struct curses_window *win, int key);

void 	       	curses_files_run(struct curses_window *win, struct node *node);
size_t			curses_delete(struct curses_window *win, struct node *node);

#endif
