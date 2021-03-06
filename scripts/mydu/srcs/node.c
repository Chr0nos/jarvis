#include "mydu.h"
#include <dirent.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <errno.h>

enum e_iter_job	node_iter(const size_t mode,
	struct node *node,
	void *userdata,
	size_t level,
	enum e_iter_job (*f)(size_t, struct node *, void *))
{
	struct s_list		*lst;
	enum e_iter_job		ret = CONTINUE;

	if (mode & PREFIX)
	{
		ret = f(level, node, userdata);
		if (ret != CONTINUE)
			return (ret == STOP_NODE ? CONTINUE : STOP_TREE);
	}
	for (lst = node->childs; lst; lst = lst->next)
	{
		ret = node_iter(mode, lst->content, userdata, level + 1, f);
		if (ret != CONTINUE)
			return (ret == STOP_NODE ? CONTINUE : STOP_TREE);
	}
	if ((mode & SUFFIX) && (ret != STOP_TREE))
		return (f(level, node, userdata));
	return (CONTINUE);
}

/*
** this function MUST be called in SUFFIX mode because childs have to be
** cleaned first.
*/

enum e_iter_job	node_iter_clean(size_t level, struct node *node, void *userdata)
{
	(void)level;
	if (userdata)
		*(size_t *)userdata += node->space.local;
	if (node->childs)
		ft_lstdel(&node->childs, NULL);
	ft_bzero(node, sizeof(*node));
	free(node);
	return (CONTINUE);
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

/*
** create a new struct node describing a file on the filesystem
** this function is only called if FLAG_FILES is present (option -f)
*/

static void			node_walk_file(struct node *parent,
	const struct config *cfg,
	const struct dirent *ent,
	const struct stat *st)
{
	struct node			*leaf;

	node_init(leaf = malloc(sizeof(struct node)), parent);
	if (!leaf)
	{
		if (cfg->flags & FLAG_VERBOSE)
			ft_dprintf(STDERR_FILENO, "%s\n", "Error: out of memory (leaf)\n");
		return ;
	}
	ft_snprintf(leaf->name, FILENAME_MAXLEN, "%s", ent->d_name);
	ft_snprintf(leaf->path, PATH_MAX, "%s/%s", parent->path, ent->d_name);
	leaf->space.local = (size_t)(st->st_blocks * BLK_SIZE);
	leaf->space.total = leaf->space.local;
	leaf->files = (struct nodestat){.local = 1, .total = 0};
	ft_lstpush_sort(&parent->childs,
		ft_lstnewlink(leaf, sizeof(*leaf)), cfg->sorter);
}

static inline void	node_walk_loop(struct node *node,
	const struct dirent *ent, struct stat *st,
	const struct config *cfg)
{
	struct node     *newnode;

	if (lstat(node->path, st) < 0)
	{
		if (cfg->flags & FLAG_VERBOSE)
			ft_dprintf(STDERR_FILENO, "failed to stat: %s: %s\n",
				node->path, strerror(errno));
		return ;
	}
	if (st->st_mode & S_IFDIR)
	{
		newnode = node_walk(node->path, node, cfg);
		if (!newnode)
			return ;
		ft_snprintf(newnode->name, FILENAME_MAXLEN, "%s", ent->d_name);
		ft_lstpush_sort(&node->childs, ft_lstnewlink(newnode, 0), cfg->sorter);
	}
	else if (st->st_mode & S_IFREG)
	{
		node->space.local += (size_t)st->st_blocks * BLK_SIZE;
		node->files.local += 1;
		if (cfg->flags & FLAG_FILES)
			node_walk_file(node, cfg, ent, st);
	}
}

/*
** TODO : use unix_walk to iterate over the filesystem to reduce the size of
** this function.
*/

__attribute((pure))
struct node  *node_walk(const char *path, struct node *parent,
	const struct config *cfg)
{
	struct node     *node;
	struct dirent   *ent;
	struct stat     st;
	DIR             *dir;

	if (node_init(node = malloc(sizeof(struct node)), parent) != EXIT_SUCCESS)
		return (NULL);
	if (!parent)
		ft_strcpy(node->name, &path[(node->name[0] == '/') ? 1 : 0]);
	dir = opendir(path);
	if (!dir)
	{
		if ((!parent) || (cfg->flags & FLAG_VERBOSE))
			ft_dprintf(STDERR_FILENO, "failed to opendir: %s: %s\n", path, strerror(errno));
		free(node);
		return NULL;
	}
	while ((ent = readdir(dir)) != NULL)
	{
		if ((ent->d_name[0] == '.') && (!(cfg->flags & FLAG_HIDENS)))
			continue ;
		if ((!ft_strcmp(ent->d_name, "..")) || (!ft_strcmp(ent->d_name, ".")))
			continue ;
		ft_snprintf(node->path, PATH_MAX, "%s/%s", path, ent->d_name);
		node_walk_loop(node, ent, &st, cfg);
	}
	closedir(dir);
	node_update_parent(node);
	node->path_len = ft_strlen(path);
	ft_memcpy(node->path, path, node->path_len + 1);
	return node;
}

/*
** puts the full path of "node" into "buffer" at max size of "n"
** return the ammount of chars wrote into buffer.
*/

size_t	node_path(const struct node *node, char *buffer, size_t n)
{
	size_t	len;

	if ((!n) || (!buffer) || (!node))
		return (0);
	if (!node->parent)
		ft_bzero(buffer, n);
	else
	{
		len = node_path(node->parent, buffer, n);
		if (len > n)
			n = 0;
		else
			n -= len;
	}
	len = (size_t)ft_snprintf(buffer, n, "%s/%s", buffer, node->name);
	return (len);
}

/*
** substract deltas to all parents of a node, node included.
*/

void	node_update_tree(struct node *node,
	const size_t delta_files, const size_t delta_size)
{
	while (node)
	{
		node->files.total -= delta_files;
		node->space.total -= delta_size;
		node = node->parent;
	}
}
