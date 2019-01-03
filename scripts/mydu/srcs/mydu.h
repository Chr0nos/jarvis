#ifndef MYDU_H
# define MYDU_H
# include <string.h>
# include <limits.h>
# include "libft.h"

# define FLAG_FULLPATH_DISPLAY	(1u << 0)
# define FLAG_LOCALSTAT			(1u << 1)
# define FLAG_REVERSE			(1u << 2)
# define FLAG_EMPTY_NODES		(1u << 3)
# define FLAG_ASCSV				(1u << 4)
# define FLAG_VERBOSE			(1u << 5)
# define FLAG_BLOCKS			(1u << 6)
# define FLAG_CURSES			(1u << 7)
# define BLK_SIZE				512
# define FILENAME_MAXLEN		256

# define PREFIX 1
# define SUFFIX 2

struct config {
	const char		*root;
	size_t			flags;
	size_t			path_len_align;
	size_t			maxlen;
	size_t			maxlevel;
	int				(*sorter)(struct s_list *, struct s_list *);
};

struct nodestat {
	size_t			local;
	size_t			total;
};

struct node {
	struct node     *parent;
	struct s_list   *childs;
	char            path[PATH_MAX];
	char			name[FILENAME_MAXLEN];
	size_t			path_len;
	struct nodestat	space;
	struct nodestat	files;
	size_t			flags;
};

enum e_iter_job {
	CONTINUE,
	STOP_NODE,
	STOP_TREE
};

#pragma pack(push, 4)

struct parser_entry {
	const int		letter;
	const char		*name;
	const size_t	flags;
	const size_t	mask;

};

#pragma pack(pop)

#define PARSER_ENTRIES 8

static const struct parser_entry g_parsing_table[PARSER_ENTRIES] = {
	(struct parser_entry){'p', "full-path", FLAG_FULLPATH_DISPLAY, 0},
	(struct parser_entry){'r', "reverse", FLAG_REVERSE, 0},
	(struct parser_entry){'l', "local", FLAG_LOCALSTAT, 0},
	(struct parser_entry){'e', "empty", FLAG_EMPTY_NODES, 0},
	(struct parser_entry){'c', "csv", FLAG_ASCSV, FLAG_LOCALSTAT},
	(struct parser_entry){'v', "verbose", FLAG_VERBOSE, 0},
	(struct parser_entry){'b', "blocks", FLAG_BLOCKS, 0},
	(struct parser_entry){'i', "interactive", FLAG_CURSES, FLAG_VERBOSE}
};

struct node		*node_walk(const char *path, struct node *parent,
	const struct config *cfg);
enum e_iter_job	node_iter_clean(size_t level, struct node *node, void *unused);
enum e_iter_job	node_iter(const size_t mode, struct node *node, void *userdata,
	size_t level, enum e_iter_job (*f)(size_t, struct node *, void *));

int				parser(int ac, char **av, struct config *cfg);
int     		lst_cmp(t_list *a, t_list *b);
int				lst_revcmp(t_list *a, t_list *b);

int	 	 		curses_run(struct node *root, const struct config *cfg);

#endif
