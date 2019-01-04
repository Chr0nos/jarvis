NAME=mydu
CFLAGS=-Wall -Werror -Wextra -Weverything -Wpedantic -Ofast
CC=clang
LIBFT_DIR=./libft
LIBFT=$(LIBFT_DIR)/libft.a
SRCS=mydu.c parser.c node.c curses.c curses_confirm.c curses_main.c
BUILD_DIR=./build
OBJS=$(SRCS:%.c=$(BUILD_DIR)/%.o)

all: $(NAME)

$(NAME): $(LIBFT) $(BUILD_DIR) $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -L $(LIBFT_DIR) -o $(NAME) -lft -lcurses

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

.PHONY: clean fclean all re install
