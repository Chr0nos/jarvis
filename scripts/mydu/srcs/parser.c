#include "mydu.h"

static int		parser_loop(const char *input, struct config *cfg)
{
	const struct parser_entry		*ent;
	size_t							p;

	p = 0;
	while (p < PARSER_ENTRIES)
	{
		ent = &g_parsing_table[p];
		if (ent->letter == (int)input[1])
		{
			cfg->flags |= ent->flags;
			cfg->flags &= ~ent->mask;
			return (EXIT_SUCCESS);
		}
		p++;
	}
	return (EXIT_FAILURE);
}

static int	parser_loadcwd(struct config *cfg)
{
	char		*cwd;

	cwd = malloc(sizeof(char) * PATH_MAX);
	if (!cwd)
		return (EXIT_FAILURE);
	cfg->flags |= FLAG_FREEROOT;
	cfg->root = getcwd(cwd, PATH_MAX);
	return (EXIT_SUCCESS);
}

int		parser(int ac, char **av, struct config *cfg)
{
	int		idx;

	ft_bzero(cfg, sizeof(*cfg));
	if (ac < 2)
	{
		ft_printf("usage: %s <path>\n", av[0]);
		return (EXIT_FAILURE);
	}
	cfg->path_len_align = 42;
	cfg->maxlen = 170;
	cfg->maxlevel = (size_t)-1;
	cfg->sorter = &lst_cmp;
	for (idx = 1; idx < ac; idx++)
	{
		if (av[idx][0] != '-')
			cfg->root = av[idx];
		else if (parser_loop(av[idx], cfg) == EXIT_SUCCESS)
			;
		else if (ft_sscanf(av[idx], "--max-level=%lu", &cfg->maxlevel) == 1)
			;
		else
			cfg->root = av[idx];
	}
	if (cfg->flags & FLAG_REVERSE)
		cfg->sorter = &lst_revcmp;
	if (!cfg->root)
		return (parser_loadcwd(cfg));
	return (EXIT_SUCCESS);
}
