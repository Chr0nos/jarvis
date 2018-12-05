/*
** Author : Chr0nos
** Compilation:
**    cd to this script dir
**    git clone https://github.com/Chr0nos/libft
**    clang mydu.c -I ./libft/include -L ./libft/ -lft -Weverything -Ofast
** What is it ?
**     this is a little .c program i'm using to find quickly big folders on
**     a computer, it's sorting the output by order of size and is not dumb as
**     "du -h" is.
** License:
**     GPLv3+
*/

#include <sys/stat.h>
#include <dirent.h>
#include <fcntl.h>
#include <limits.h>
#include <errno.h>
#include <string.h>
#include "libft.h"

#define FLAG_FULLPATH_DISPLAY	(1u << 0)
#define FLAG_LOCALSTAT			(1u << 1)
#define FLAG_REVERSE			(1u << 2)
#define FLAG_EMPTY_NODES		(1u << 3)
#define FLAG_ASCSV				(1u << 4)
#define FILENAME_MAX			256

struct config {
	const char		*root;
	size_t			flags;
	size_t			path_len_align;
	size_t			maxlen;
	size_t			maxlevel;
};

struct node {
	struct node     *parent;
	struct s_list   *childs;
	char            path[PATH_MAX];
	char			name[FILENAME_MAX];
	size_t			path_len;
	size_t          space;
	size_t          total_space;
	size_t          files;
	size_t          total_files;
};

#pragma pack(push, 4)

struct parser_entry {
	const int		letter;
	const char		*name;
	const size_t	flags;
	const size_t	mask;

};

#pragma pack(pop)

#define PARSER_ENTRIES 5

static const struct parser_entry g_parsing_table[PARSER_ENTRIES] = {
	(struct parser_entry){'p', "full-path", FLAG_FULLPATH_DISPLAY, 0},
	(struct parser_entry){'r', "reverse", FLAG_REVERSE, 0},
	(struct parser_entry){'l', "local", FLAG_LOCALSTAT, 0},
	(struct parser_entry){'e', "empty", FLAG_EMPTY_NODES, 0},
	(struct parser_entry){'c', "csv", FLAG_ASCSV, FLAG_LOCALSTAT}
};

/*
** i'm forced to declare this static prototype for usage in node_walk_loop
*/

static struct node  *node_walk(const char *path, struct node *parent,
	const struct config *cfg);

static int      node_cmp(struct node *a, struct node *b)
{
	if (a->total_space < b->total_space)
		return (1);
	else if (a->total_space > b->total_space)
		return (-1);
	return (ft_strcmp(a->path, b->path));
}

static int      lst_cmp(t_list *a, t_list *b)
{
	return (node_cmp(a->content, b->content));
}

static int		lst_revcmp(t_list *a, t_list *b)
{
	return (-node_cmp(a->content, b->content));
}

static inline void  node_update_parent(struct node *node)
{
	node->total_space += node->space;
	node->total_files += node->files;
	if (node->parent)
	{
		node->parent->total_files += node->total_files;
		node->parent->total_space += node->total_space;
	}
}

static inline int   node_init(struct node *node, struct node *parent)
{
	if (!node)
	{
		ft_dprintf(STDERR_FILENO, "%s", "Error: out of memory\n");
		return (EXIT_FAILURE);
	}
	ft_bzero(node, sizeof(*node));
	node->parent = parent;
	return (EXIT_SUCCESS);
}

static inline void	node_walk_loop(struct node *node,
	const struct dirent *ent, struct stat *st,
	const struct config *cfg)
{
	struct node     *newnode;

	if (lstat(node->path, st) < 0)
		return ;
	if (st->st_mode & S_IFDIR)
	{
		newnode = node_walk(node->path, node, cfg);
		if (!newnode)
			return ;
		ft_snprintf(newnode->name, FILENAME_MAX, "%s", ent->d_name);
		ft_lstpush_sort(&node->childs, ft_lstnewlink(newnode, 0),
			(cfg->flags & FLAG_REVERSE) ? lst_revcmp : lst_cmp);
	}
	else if (st->st_mode & S_IFREG)
	{
		if (st->st_size > 0)
			node->space += (size_t)st->st_size;
		node->files += 1;
	}
}

static struct node  *node_walk(const char *path, struct node *parent,
	const struct config *cfg)
{
	struct node     *node;
	struct dirent   *ent;
	struct stat     st;
	DIR             *dir;

	if (node_init(node = malloc(sizeof(struct node)), parent) != EXIT_SUCCESS)
		return (NULL);
	if (!parent)
		ft_strcpy(node->name, &path[1]);
	dir = opendir(path);
	if (!dir)
	{
		if (!parent)
			ft_dprintf(2, "failed to opendir: %s\n", path);
		free(node);
		return NULL;
	}
	while ((ent = readdir(dir)) != NULL)
	{
		if (ent->d_name[0] == '.')
			continue ;
		ft_snprintf(node->path, PATH_MAX, "%s/%s", path, ent->d_name);
		node_walk_loop(node, ent, &st, cfg);
	}
	closedir(dir);
	node_update_parent(node);
	node->path_len = ft_strlen(path);
	ft_strcpy(node->path, path);
	return node;
}

static void show_human(struct s_printf *pf)
{
	size_t              len;
	char                buf[80];

	len = ft_printf_append(pf, buf,
		(size_t)ft_wsize((size_t)pf->raw_value, buf, 80));
	pf->slen += len;
}

static void node_iter_show(size_t level, struct node *node, void *config)
{
	struct config	*cfg = config;
	char			path[PATH_MAX];

	if ((node->total_files == 0) && (!(cfg->flags & FLAG_EMPTY_NODES)))
		return ;
	if (level > cfg->maxlevel)
		return ;
	if (cfg->flags & FLAG_FULLPATH_DISPLAY)
		ft_memcpy(path, node->path, node->path_len + 1);
	else
		ft_snprintf(path, PATH_MAX, "%-*.1hhk/%s",
			level * 2, ft_printf_conv_padding, ' ', node->name);
	ft_printf("%-*s : %-8.2lk : %lu\n",
		cfg->path_len_align,
		path, show_human,
		(cfg->flags & FLAG_LOCALSTAT) ? node->space : node->total_space,
		(cfg->flags & FLAG_LOCALSTAT) ? node->files : node->total_files);
}

static void	node_iter_csv(size_t level, struct node *node, void *config)
{
	(void)config;
	ft_printf("%lu,%s,%s,%lu,%lu,%lu,%lu\n",
		level, node->name, node->path, node->total_space, node->total_files,
		node->space, node->files);
}

/*
** get the max path lenght
** this is need for alignment purposes
*/

static void	node_iter_get_maxpl(size_t level, struct node *node, void *config)
{
	struct config	*cfg = config;
	size_t			len;

	len	= (cfg->flags & FLAG_FULLPATH_DISPLAY)
		? node->path_len : (ft_strlen(node->name) + (level * 2));
	if (len > cfg->path_len_align)
	{
		if (len > cfg->maxlen)
			cfg->path_len_align = cfg->maxlen;
		else
			cfg->path_len_align = len;
	}
}

#define PREFIX 1
#define SUFFIX 2

static void	node_iter(const size_t mode,
	struct node *node,
	void *userdata,
	size_t level,
	void (*f)(size_t, struct node *, void *))
{
	struct s_list	*lst;

	if (mode & PREFIX) 
		f(level, node, userdata);
	for (lst = node->childs; lst; lst = lst->next)
		node_iter(mode, lst->content, userdata, level + 1, f);
	if (mode & SUFFIX)
		f(level, node, userdata);
}

static void	node_iter_clean(size_t level, struct node *node, void *unused)
{
	(void)level;
	(void)unused;
	if (node->childs)
		ft_lstdel(&node->childs, NULL);
	free(node);
}

static int		parser_loop(const char *input, struct config *cfg)
{
	const struct parser_entry		*ent;
	size_t							p;

	p = 0;
	while (p < PARSER_ENTRIES)
	{
		ent = &g_parsing_table[p];
		if (ent->letter == (int)input[1])
		{
			cfg->flags |= ent->flags;
			cfg->flags &= ~ent->mask;
			return (EXIT_SUCCESS);
		}
		p++;
	}
	return (EXIT_FAILURE);
}

static int		parser(int ac, char **av, struct config *cfg)
{
	int		idx;

	ft_bzero(cfg, sizeof(*cfg));
	if (ac < 2)
	{
		ft_printf("usage: %s <path>\n", av[0]);
		return (EXIT_FAILURE);
	}
	cfg->path_len_align = 42;
	cfg->maxlen = 170;
	cfg->maxlevel = (size_t)-1;
	for (idx = 1; idx < ac; idx++)
	{
		if (av[idx][0] != '-')
			cfg->root = av[idx];
		else if (parser_loop(av[idx], cfg) == EXIT_SUCCESS)
			;
		else if (ft_sscanf(av[idx], "--max-level=%lu", &cfg->maxlevel) == 1)
			;
		else
			cfg->root = av[idx];
	}
	if (!cfg->root)
		return (EXIT_FAILURE);
	return (EXIT_SUCCESS);
}

int     main(int ac, char **av)
{
	struct config	cfg;
	struct node     *node;
	size_t			dorder = PREFIX;

	if (parser(ac, av, &cfg) != EXIT_SUCCESS)
		return (EXIT_FAILURE);
	node = node_walk(cfg.root, NULL, &cfg);
	if (cfg.flags & FLAG_REVERSE)
		dorder = SUFFIX;
	if (!node)
	{
		ft_dprintf(STDERR_FILENO, "%s%s\n", "Error: ", strerror(errno));
		return (EXIT_FAILURE);
	}
	node_iter(PREFIX, node, &cfg, 0, node_iter_get_maxpl);
	node_iter(dorder, node, &cfg, 0,
		(cfg.flags & FLAG_ASCSV) ? node_iter_csv : node_iter_show);
	node_iter(SUFFIX, node, NULL, 0, node_iter_clean);
	return (EXIT_SUCCESS);
}
