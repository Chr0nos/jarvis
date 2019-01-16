NAME=mydu
CC=clang
OS=$(shell uname -s)
CFLAGS=-Wall -Werror -Wextra -Weverything -Wpedantic -Ofast
LINKER=-lft
LIBFT_DIR=./libft
LIBFT=$(LIBFT_DIR)/libft.a
SRCS=mydu.c parser.c node.c curses.c curses_confirm.c curses_main.c \
	curses_window.c curses_files.c curses_delete.c unix_walk.c curses_info.c
BUILD_DIR=./build
OBJS=$(SRCS:%.c=$(BUILD_DIR)/%.o)

ifeq ($(OS), Darwin)
	LINKER+=-lcurses
else
	LINKER+=-lncursesw
endif

all: $(NAME)

$(NAME): $(LIBFT) $(BUILD_DIR) $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -L $(LIBFT_DIR) -o $(NAME) $(LINKER)

$(BUILD_DIR)/%.o: ./srcs/%.c
	$(CC) $(CFLAGS) -I $(LIBFT_DIR)/include -c $< -o $@

$(BUILD_DIR):
	mkdir -pv $(BUILD_DIR)

$(LIBFT_DIR):
	git clone https://github.com/Chr0nos/libft

$(LIBFT): $(LIBFT_DIR)
	make -C $(LIBFT_DIR) -j

clean:
	$(RM) -r $(BUILD_DIR)

fclean: clean
	$(RM) $(NAME)

re: fclean all

install: $(NAME)
	sudo cp -v $(NAME) /usr/bin

test:
	clang -I$(LIBFT_DIR)/include srcs/unix_walk.c srcs/test_unix.c -L$(LIBFT_DIR) $(LINKER) -o test

.PHONY: clean fclean all re install
