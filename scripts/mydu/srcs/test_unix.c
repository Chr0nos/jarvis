#include "mydu.h"

int     main(int ac, char **av)
{
    if (ac < 2)
        return (1);
    unix_walk(SUFFIX, av[1], NULL, unix_display, NULL);
    return (0);
}
