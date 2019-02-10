NAME=mydu
CC=clang
OS=$(shell uname -s)
CFLAGS=-Wall -Werror -Wextra -Weverything -Wpedantic -Ofast
LINKER=-lft -lcursed -lpthread

LIBFT_DIR=./libs/libft
LIBFT=$(LIBFT_DIR)/libft.a

LIBCURSED_DIR=./libs/libcursed
LIBCURSED=$(LIBCURSED_DIR)/libcursed.a

INC=-I $(LIBFT_DIR)/include -I $(LIBCURSED_DIR)/srcs

SRCS=mydu.c parser.c node.c curses.c curses_main.c \
	curses_files.c curses_delete.c unix_walk.c  \
	curses_fileinfo.c
BUILD_DIR=./build
OBJS=$(SRCS:%.c=$(BUILD_DIR)/%.o)

ifeq ($(OS), Darwin)
	LINKER+=-lcurses
else
	LINKER+=-lncursesw
endif

all: $(NAME)

$(NAME): $(LIBFT) $(LIBCURSED) $(BUILD_DIR) $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -L $(LIBFT_DIR) -L $(LIBCURSED_DIR) -o $(NAME) $(LINKER)

$(BUILD_DIR)/%.o: ./srcs/%.c
	$(CC) $(CFLAGS) $(INC) -c $< -o $@

$(BUILD_DIR):
	mkdir -pv $(BUILD_DIR)

$(LIBFT_DIR):
	git clone https://github.com/Chr0nos/libft

$(LIBFT): $(LIBFT_DIR)
	make -C $(LIBFT_DIR) -j

$(LIBCURSED): $(LIBCURSED_DIR)
	make -C $(LIBCURSED_DIR) -j

$(LIBCURSED_DIR):
	git clone https://github.com/Chr0nos/libcursed.git

clean:
	$(RM) -r $(BUILD_DIR)

fclean: clean
	$(RM) $(NAME)

re: fclean all

install: $(NAME)
	sudo cp -v $(NAME) /usr/bin

test:
	clang -I$(LIBFT_DIR)/include srcs/unix_walk.c srcs/test_unix.c -L$(LIBFT_DIR) $(LINKER) -o test

mrproper: fclean
	make -C $(LIBFT_DIR) fclean
	make -C $(LIBCURSED_DIR) fclean

.PHONY: clean fclean all re install
