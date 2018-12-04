#include <sys/stat.h>
#include <dirent.h>
#include <fcntl.h>
#include <limits.h>
#include <errno.h>
#include <string.h>
#include "libft.h"

#define FLAG_FULLPATH_DISPLAY	(1u << 0)
#define FLAG_LOCALSIZE			(1u << 1)

struct config {
	const char		*root;
	size_t			level;
	size_t			flags;
};

struct node {
	struct node     *parent;
	struct s_list   *childs;
	char            path[PATH_MAX];
	size_t          space;
	size_t          total_space;
	size_t          files;
	size_t          total_files;
};

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

static inline void  node_update_parent(struct node *node)
{
	if (node->parent)
	{
		node->parent->total_files += node->total_files;
		node->parent->total_space += node->total_space;
	}
}

static inline int   node_init(struct node *node, struct node *parent)
{
	if (!node)
		return (EXIT_FAILURE);
	ft_bzero(node, sizeof(*node));
	node->parent = parent;
	return (EXIT_SUCCESS);
}

static struct node  *node_walk(const char *path, struct node *parent)
{
	struct node     *node;
	struct node     *newnode;
	struct dirent   *ent;
	struct stat     st;
	DIR             *dir;

	if (node_init(node = malloc(sizeof(struct node)), parent) != EXIT_SUCCESS)
		return (NULL);
	dir = opendir(path);
	if (!dir)
	{
		free(node);
		return NULL;
	}
	while ((ent = readdir(dir)) != NULL)
	{
		if (ent->d_name[0] == '.')
			continue ;
		ft_snprintf(node->path, PATH_MAX, "%s/%s", path, ent->d_name);
		if (ent->d_type & DT_DIR)
		{
			newnode = node_walk(node->path, node);
			if (!newnode)
				continue ;
			ft_lstpush_sort(&node->childs, ft_lstnewlink(newnode, 0), lst_cmp);
		}
		else if (stat(node->path, &st) >= 0)
		{
			node->space += (size_t)st.st_size;
			node->files += 1;
		}
	}
	closedir(dir);
	node->total_space += node->space;
	node->total_files += node->files;
	node_update_parent(node);
	ft_strcpy(node->path, path);
	return node;
}

static int	wsize(const size_t size, char *buf, const size_t n)
{
	double	x;
	size_t	unit;

	x = (double)size;
	unit = 0;
	while ((x >= 1024.0) && (unit < 7))
	{
		x /= 1024.0;
		unit++;
	}
	return (ft_snprintf(buf, n, "%.2f%c", x, "bKMGTPE"[unit]));
}

static void show_human(struct s_printf *pf)
{
	const size_t        align = 6;
	size_t              len;
	char                buf[80];

	len = ft_printf_append(pf, buf,
		(size_t)wsize((size_t)pf->raw_value, buf, 80));
	pf->slen += len;
	if (len < align)
		ft_printf_padding(pf, ' ', (int)(align - len));
}

static size_t strcmplen(const char *sa, const char *sb)
{
	size_t		len;

	for (len = 0; sa[len] && sa[len] == sb[len]; len++)
		;
	return (len);
}

static void node_show(void *config, size_t size, void *content)
{
	struct config	*cfg = config;
	struct node     *node = content;
	char			path[PATH_MAX];

	(void)size;
	ft_strcpy(path, node->path);
	if ((!(cfg->flags & FLAG_FULLPATH_DISPLAY)) && (node->parent))
		memset(path, ' ', strcmplen(node->path, node->parent->path));
	ft_printf("%-72s : %20lk : %-6lu\n", path, show_human,
		(cfg->flags & FLAG_LOCALSIZE) ? node->space : node->total_space,
		node->total_files);
	cfg->level++;
	ft_lstforeach(node->childs, cfg, node_show);
	cfg->level--;
}

static void node_clean(void *userdata, size_t size, void *content)
{
	struct node     *node = content;

	(void)userdata;
	(void)size;
	if (node->childs)
	{
		ft_lstforeach(node->childs, NULL, node_clean);
		ft_lstdel(&node->childs, NULL);
	}
	free(node);
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
	for (idx = 1; idx < ac; idx++)
	{
		if (av[idx][0] != '-')
			cfg->root = av[idx];
		else if (!ft_strcmp(av[idx], "-p"))
			cfg->flags |= FLAG_FULLPATH_DISPLAY;
		else if (!ft_strcmp(av[idx], "-l"))
			cfg->flags |= FLAG_LOCALSIZE;
	}
	return (EXIT_SUCCESS);
}

int     main(int ac, char **av)
{
	struct config	cfg;
	struct node     *node;

	if (parser(ac, av, &cfg) != EXIT_SUCCESS)
		return (EXIT_FAILURE);
	node = node_walk(cfg.root, NULL);
	if (!node)
	{
		ft_dprintf(STDERR_FILENO, "%s%s\n", "Error: ", strerror(errno));
		return (EXIT_FAILURE);
	}
	node_show(&cfg, 0, node);
	node_clean(NULL, 0, node);
	return (EXIT_SUCCESS);
}
