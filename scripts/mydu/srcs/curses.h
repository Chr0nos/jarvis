#ifndef CURSES_H
# define CURSES_H
# include <ncurses.h>
# include <sys/param.h>
# include <sys/mount.h>
# ifdef linux
#  include <sys/statfs.h>
# endif
# include "cursed.h"
# include "mydu.h"

# define WSIZE_LEN			16

# define BACKSPACE       	127

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
	struct node				*node;
	struct s_list			*content;
	struct statfs			fs;
	char					title[PATH_MAX];
	struct file_entry		*selected;
	size_t					selected_index;
	char					**environement;
	bool					xdg_open;
	bool					padding[7];
};

struct deletion_task {
	struct node				*node;
	size_t					deleted_items;
	size_t					deleted_size;
};

/*
** mydu ncurses mode specific functions
*/

int	 	 		curses_run(struct node *root, const struct config *cfg);
void 	       	curses_files_run(struct curses_window *win, struct node *node);
size_t			curses_delete(struct curses_window *win, struct node *node);
void        	curses_filefinfo(struct curses_window *win, struct file_entry *file);


/*
** function about the main window
*/

int				main_window_init(struct curses_window *win);
int         	main_window_draw(struct curses_window *win);
int   			main_window_input(struct curses_window *win, int key);

t_list	        *lst_search_content(struct s_list *lst, const void *content);

#endif
