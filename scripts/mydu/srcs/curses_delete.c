#include "mydu.h"
#include <unistd.h>
#include <pthread.h>

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

static void				*delete_task(void *userdata)
{
	struct deletion_task	*task = userdata;

	unix_walk(SUFFIX, task->node->path, &task->deleted_items,
		&curses_delete_files, NULL);
	node_iter(SUFFIX, task->node, NULL, 0, &node_iter_clean);
	return (NULL);
}

static void				*spawn_window(void *userdata)
{
	curses_new_window(userdata);
	return (NULL);
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
	struct curses_window	wait_window;
	char					confirm_title[PATH_MAX];
	pthread_t				deletion_thread;
	pthread_t				wait_win_thread;
	struct deletion_task	task;

	if (!node)
		return (0);
	ft_snprintf(confirm_title, PATH_MAX, "%s%c%s%c ?", "Delete all content of ",
		'"', node->path, '"');
	if (!curses_confirm(win, confirm_title, false))
		return (0);
	wait_window = (struct curses_window) {
		.parent = win,
		.x = (win->w >> 1),
		.y = (win->h >> 1),
		.w = 60,
		.h = 8,
		.flags = WIN_NOQ | WIN_NOINPUT,
		.title = "Please wait during deletions...",
	};
	task = (struct deletion_task) {
		.node = node,
		.deleted_items = 0
	};
	win->flags |= WIN_NOQ;
	pthread_create(&deletion_thread, NULL, &delete_task, &task);
	pthread_create(&wait_win_thread, NULL, &spawn_window, &wait_window);
	pthread_join(deletion_thread, NULL);
	wait_window.flags |= WIN_QUIT;
	pthread_join(wait_win_thread, NULL);
	win->flags &= ~WIN_NOQ;
	return (task.deleted_items);
}
