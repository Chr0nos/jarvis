/*
** Author : Chr0nos
** Compilation:
**     just type "make"
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
#include <errno.h>
#include "mydu.h"

/*
** i'm forced to declare this static prototype for usage in node_walk_loop
*/

static struct node  *node_walk(const char *path, struct node *parent,
	const struct config *cfg);

__attribute((pure))
static int      node_cmp(struct node *a, struct node *b)
{
	if (a->space.total < b->space.total)
		return (1);
	else if (a->space.total > b->space.total)
		return (-1);
	return (ft_strcmp(a->path, b->path));
}

__attribute((pure))
int      lst_cmp(t_list *a, t_list *b)
{
	return (node_cmp(a->content, b->content));
}

__attribute((pure))
int		lst_revcmp(t_list *a, t_list *b)
{
	return (-node_cmp(a->content, b->content));
}

static inline void  node_update_parent(struct node *node)
{
	node->space.total += node->space.local;
	node->files.total += node->files.local;
	if (node->parent)
	{
		node->parent->files.total += node->files.total;
		node->parent->space.total += node->space.total;
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
		ft_lstpush_sort(&node->childs, ft_lstnewlink(newnode, 0), cfg->sorter);
	}
	else if (st->st_mode & S_IFREG)
	{
		if (st->st_size > 0)
			node->space.local += (size_t)st->st_size;
		node->files.local += 1;
	}
}

__attribute((pure))
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

static void node_iter_show(size_t level, struct node *node, void *config)
{
	struct config	*cfg = config;
	char			path[PATH_MAX];

	if ((node->files.total == 0) && (!(cfg->flags & FLAG_EMPTY_NODES)))
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

		path, ft_printf_conv_wsize,
		(cfg->flags & FLAG_LOCALSTAT) ? node->space.local : node->space.total,
		(cfg->flags & FLAG_LOCALSTAT) ? node->files.local : node->files.total);
}

static void	node_iter_csv(size_t level, struct node *node, void *config)
{
	(void)config;
	ft_printf("%lu,%s,%s,%lu,%lu,%lu,%lu\n",
		level, node->name, node->path, node->space.total, node->files.total,
		node->space.local, node->files.local);
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
		cfg->path_len_align = (len > cfg->maxlen) ? cfg->maxlen : len;
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
