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

#include <errno.h>
#include "mydu.h"

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

static enum e_iter_job node_iter_show(size_t level, struct node *node,
	void *config)
{
	struct config	*cfg = config;
	char			path[PATH_MAX];

	if ((node->files.total == 0) && (!(cfg->flags & FLAG_EMPTY_NODES)))
		return (CONTINUE);
	if (level > cfg->maxlevel)
		return (CONTINUE);
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
	return (CONTINUE);
}

static enum e_iter_job	node_iter_csv(size_t level, struct node *node,
	void *config)
{
	(void)config;
	ft_printf("%lu,%s,%s,%lu,%lu,%lu,%lu\n",
		level, node->name, node->path, node->space.total, node->files.total,
		node->space.local, node->files.local);
	return (CONTINUE);
}

/*
** get the max path lenght
** this is need for alignment purposes
*/

static enum e_iter_job	node_iter_get_maxpl(size_t level, struct node *node,
	void *config)
{
	struct config	*cfg = config;
	size_t			len;

	if (cfg->maxlevel < level)
		return (CONTINUE);
	len	= (cfg->flags & FLAG_FULLPATH_DISPLAY)
		? node->path_len : (ft_strlen(node->name) + (level * 2));
	if (len > cfg->path_len_align)
		cfg->path_len_align = (len > cfg->maxlen) ? cfg->maxlen : len;
	return (CONTINUE); 
}

static int		display(struct node *node, struct config *cfg)
{
	size_t			dorder = PREFIX;

	if (cfg->flags & FLAG_CURSES)
		return (curses_run(node, cfg));
	if (cfg->flags & FLAG_REVERSE)
		dorder = SUFFIX;
	node_iter(PREFIX, node, cfg, 0, node_iter_get_maxpl);
	node_iter(dorder, node, cfg, 0,
		(cfg->flags & FLAG_ASCSV) ? node_iter_csv : node_iter_show);
	node_iter(SUFFIX, node, NULL, 0, node_iter_clean);
	return (EXIT_SUCCESS);
}

int     main(int ac, char **av)
{
	struct config	cfg;
	struct node     *node;

	if (parser(ac, av, &cfg) != EXIT_SUCCESS)
		return (EXIT_FAILURE);
	node = node_walk(cfg.root, NULL, &cfg);
	if (!node)
	{
		ft_dprintf(STDERR_FILENO, "%s%s\n", "Error: ", strerror(errno));
		return (EXIT_FAILURE);
	}
	return (display(node, &cfg));
}
