#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <sys/types.h>
#include <unistd.h>
#include <linux/limits.h>

#define PATH "/dev/disk/by-label/"

static void	read_loop(DIR *d)
{
	struct dirent	*dir;
	char			filepath[PATH_MAX];
	char			link[PATH_MAX];
	ssize_t			len;

	printf("%-20s  %-17s %s\n%s\n", "Label", "Device", "Mount command",
		"-------------------------------------------------------------------");
	while ((dir = readdir(d)) != NULL)
	{
		if (dir->d_name[0] == '.')
			continue ;
		snprintf(filepath, 1024, "%s%s", PATH, dir->d_name);
		len = readlink(filepath, link, 1023);
		if (len < 0)
			continue ;
		link[len] = '\0';
		printf("%-20s %s%-12s %s%s\n", dir->d_name, "/dev/", &link[6],
			"udisksctl mount -b /dev/", &link[6]);
	}
}

int			main(void)
{
	DIR		*d;

	d = opendir(PATH);
	if (!d)
	{
		dprintf(STDERR_FILENO, "%s\n", "Error: failed to open dir");
		return (EXIT_FAILURE);
	}
	read_loop(d);
	closedir(d);	
	return (EXIT_SUCCESS);	
}
