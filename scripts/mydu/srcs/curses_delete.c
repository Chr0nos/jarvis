#include "mydu.h"
#include <unistd.h>

static void				curses_delete_files(
	const char *path,
	struct stat *st,
	__attribute((unused)) struct dirent *ent,
	void *userdata)
{
	int			ret;

	if (st->st_mode & S_IFDIR)
		ret = rmdir(path);
	else
		ret = unlink(path);
	if (ret < 0)
		return ;
	*((size_t*)userdata) += 1;
}

/*
** return the number of deleted files.
*/

size_t					curses_delete(struct curses_window *win, struct node *node)
{
	size_t		deleted_items = 0;
	char		buf[PATH_MAX];

	if (!node)
		return (0);
	ft_snprintf(buf, PATH_MAX, "%s%c%s%c ?", "Delete all content of ",
		'"', node->path, '"');
	if (!curses_confirm(win, buf, false))
		return (0);
	unix_walk(SUFFIX, node->path, &deleted_items, &curses_delete_files, NULL);
	node_iter(SUFFIX, node, NULL, 0, &node_iter_clean);
	return (deleted_items);
}
