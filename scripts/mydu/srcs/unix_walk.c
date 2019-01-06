#include <sys/stat.h>
#include <limits.h>
#include <unistd.h>
#include "mydu.h"

void		unix_walk(
	const size_t mode,
	const char *path,
	void *userdata,
	void (*callback)(const char *path, struct stat *st, struct dirent *ent, void *userdata),
	void (*fails)(const char *path, struct dirent *ent, void *userdata))
{
	char			fullpath[PATH_MAX];
	struct stat		st;
	DIR				*dir;
	struct dirent   *ent;

	if (mode & PREFIX)
		callback(path, (stat(path, &st) < 0) ? NULL : &st, NULL, userdata);
	dir = opendir(path);
	if (!dir)
	{
		if (fails)
			fails(path, NULL, userdata);
		return ;
	}
	while ((ent = readdir(dir)) != NULL)
	{
		if ((!ft_strcmp(ent->d_name, ".")) || (!ft_strcmp(ent->d_name, "..")))
			continue ;
		ft_snprintf(fullpath, PATH_MAX, "%s/%s", path, ent->d_name);
		if (stat(fullpath, &st) < 0)
		{
			if (fails)
				fails(fullpath, ent, userdata);
			continue ;
		}
		if ((mode & PREFIX) && (!(st.st_mode & S_IFDIR)))
			callback(fullpath, &st, ent, userdata);
		unix_walk(mode, fullpath, userdata, callback, fails);
		if ((mode & SUFFIX) && (!(st.st_mode & S_IFDIR)))
			callback(fullpath, &st, ent, userdata);
	}
	closedir(dir);
	if (mode & SUFFIX)
		callback(path, (stat(path, &st) < 0) ? NULL : &st, NULL, userdata);
}

void		unix_display(const char *path,
	__attribute((unused)) struct stat *st,
	__attribute((unused)) struct dirent *ent,
	__attribute((unused)) void *userdata)
{
	ft_printf("%s\n", path);
}
