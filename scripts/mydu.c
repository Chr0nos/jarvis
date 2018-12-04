#include <sys/stat.h>
#include <dirent.h>
#include <fcntl.h>
#include <limits.h>
#include <errno.h>
#include <string.h>
#include "libft.h"

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

static void show_human(struct s_printf *pf)
{
	const size_t        align = 6;
	size_t              len;
	char                buf[80];

	ft_wsize((unsigned long long)pf->raw_value, buf);
	len = ft_printf_append(pf, buf, ft_strlen(buf));
	pf->slen += len;
	if (len < align)
		ft_printf_padding(pf, ' ', (int)(align - len));
}

static void node_show(void *level, size_t size, void *content)
{
	struct node     *node = content;

	(void)size;
	(void)level;
	ft_printf("%-72s : %20lk : %-6lu\n", node->path, show_human,
		node->total_space,
		node->total_files);
	ft_lstforeach(node->childs, (void*)((size_t)level + 1), node_show);
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

int     main(int ac, char **av)
{
	struct node     *node;

	if (ac < 2)
	{
		ft_printf("usage: %s <path>\n", av[0]);
		return (EXIT_FAILURE);
	}
	node = node_walk(av[1], NULL);
	if (!node)
	{
		ft_dprintf(STDERR_FILENO, "%s%s\n", "Error: ", strerror(errno));
		return (EXIT_FAILURE);
	}
	node_show(0, 0, node);
	node_clean(NULL, 0, node);
	return (EXIT_SUCCESS);
}
