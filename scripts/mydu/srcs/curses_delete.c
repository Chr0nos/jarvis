#include "mydu.h"
#include <unistd.h>
#include <pthread.h>
#define WAIT_WINDOW_WIDTH	60
#define WAIT_WINDOW_HEIGH	8

/*
** note for future me:
** please don't try again to use node_iter call to perform this instead of
** unix_walk: the files are not allaws in the node tree. only the dirs are.
** save time, deal with it
** BUGS:
** this function by design may delete any new file located into the node
** the user will not see thoses files disapears, you've been warned.
*/

static void				curses_delete_files(
	const char *path,
	struct stat *st,
	__attribute((unused)) struct dirent *ent,
	void *userdata)
{
	struct deletion_task	*task = userdata;
	int						ret;

	if (st->st_mode & S_IFDIR)
		ret = rmdir(path);
	else
		ret = unlink(path);
	if (ret < 0)
		return ;
	task->deleted_items += 1;
	task->deleted_size += (size_t)st->st_blocks * BLK_SIZE;
}

static void				*delete_task(void *userdata)
{
	struct deletion_task	*task = userdata;

	unix_walk(SUFFIX, task->node->path, task, &curses_delete_files, NULL);
	node_iter(SUFFIX, task->node, NULL, 0, &node_iter_clean);
	return (NULL);
}

static int				wait_win_draw(struct curses_window *win)
{
	refresh();
	pthread_join(*(pthread_t*)win->userdata, NULL);
	win->flags |= WIN_QUIT;
	return (0);
}

/*
** return the number of deleted files.
** this function works on 2 threads:
** - one for the deletion
** - one for the waiting information window
** once the deletions are done, the window is commanded via flags to exit
** properly, the wait window cannot be exited by the user.
** since the flag is set, the thread wait to quit properly
** the parent window will be set as unquitable window to avoid crap
*/

size_t					curses_delete(struct curses_window *win, struct node *node)
{
	struct curses_window	wait;
	char					confirm_title[PATH_MAX];
	pthread_t				deletion_thread;
	struct deletion_task	task;

	if (!node)
		return (0);
	ft_snprintf(confirm_title, PATH_MAX, "%s%c%s%c ?", "Delete all content of ",
		'"', node->path, '"');
	if (!curses_confirm(win, confirm_title, false))
		return (0);
	wait = (struct curses_window) {
		.parent = win,
		.flags = WIN_NOINPUT,
		.title = "Please wait during deletions...",
		.draw = &wait_win_draw,
		.userdata = &deletion_thread
	};
	task = (struct deletion_task) {
		.node = node,
		.deleted_items = 0,
		.deleted_size = 0
	};
	pthread_create(&deletion_thread, NULL, &delete_task, &task);
	curses_centerfrom_parent(&wait, WAIT_WINDOW_HEIGH, WAIT_WINDOW_WIDTH);
	curses_new_window(&wait);
	return (task.deleted_items);
}
