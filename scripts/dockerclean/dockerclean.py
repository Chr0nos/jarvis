import docker, curses, logging
from time import sleep


def wsize(n):
    powers = ('b', 'kb', 'mb', 'gb', 'tb')
    m = len(powers)
    i = 0
    while n > 1024 and i < m:
        n /= 1024
        i += 1
    return str(round(n, 2)) + powers[i]


class Window:
    def __init__(self, parent, title: str, x: int, y: int, w: int, h: int):
        self.parent = parent
        self.title = title
        self.title_len = len(title)
        if parent is None:
            self.x = x
            self.y = y
        else:
            self.w = w
            self.h = h
            self.x = x + parent.x
            self.y = y + parent.y
            self.screen = parent.screen

    def put_center(self, content: str, y=0):
        return self.screen.addstr(
            self.h + y,
            self.x + (self.w >> 1) - (len(content) >> 1),
            content
        )

    def put(self, y, x, content: str):
        return self.screen.addstr(self.h + y, self.x + x, content)

    def decorate(self):
        self.put(0, 0, '-' * self.w)
        for line in range(0, self.h):
            self.put(line, 0, '|')
            self.put(line, self.w, '|')
        self.put(0, 0, '-' * (self.w + 1))
        self.put(self.h, 0, '-' * (self.w + 1))
        self.put_center(self.title + f' {self.w}x{self.h}')

    def clear(self):
        for line in range(self.h):
            self.put(line, 0, ' ' * self.w)

    def display(self, context=None):
        pass

    def action(self, key):
        pass

    def loop(self):
        assert self.screen
        while True:
            self.decorate()
            self.display()
            self.screen.refresh()
            key = self.screen.getkey()
            if key == 'q':
                raise KeyboardInterrupt
            self.action(key)


class MainWindow(Window):
    def __init__(self, title):
        print('init start')
        self.screen = curses.initscr()
        assert self.screen is not None
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        # super(MainWindow, self).__init__(None, title, 0, 0, curses.COLS, curses.LINES)
        Window.__init__(self, None, title, 0, 0, curses.COLS, curses.LINES)
        self.screen.keypad(True)
        print('init done')

    def __del__(self):
        self.close()

    def close(self):
        curses.nocbreak()
        self.screen.keypad(False)
        curses.echo()
        curses.endwin()

    @property
    def w(self):
        return int(curses.COLS)

    @property
    def h(self):
        return int(curses.LINES)

    def decorate(self):
        pass

    def put(self, y, x, content: str):
        return self.screen.addstr(y, x, content)

    def put_center(self, content: str, y=0):
        return self.screen.addstr(y, (self.w >> 1) - (len(content) >> 1))

    def display(self):
        pass

    def loop(self):
        while True:
            try:
                super().loop()
            except KeyboardInterrupt:
                return
            except Exception as err:
                self.screen.clear()
                self.screen.addstr(10, 10, 'error: ' + str(err))
                self.screen.refresh()
                self.screen.getch()


class DockerImagesManager(MainWindow):
    def __init__(self):
        super().__init__('Docker Images Manager')
        self.line_max = 0
        self.client = docker.from_env()
        self.setup()

    def action(self, key):
        self.screen.addstr(self.line_max + 5, 0, f'action: {key}')
        if key == 'd':
            self.delete_selection()
        if key == 'KEY_UP':
            self.line = max(self.line - 1, 0)
        if key == 'KEY_DOWN':
            self.line = min(self.line + 1, self.line_max)
        if key == 'w':
            w = Window(
                parent=self,
                title='test',
                x=(self.w >> 2),
                y=self.y + 3,
                w=(self.w >> 1),
                h=(self.h >> 1)
            )
            w.loop()

    def get_selected_id(self):
        return list(self.images.values())[self.line]

    def delete_selection(self):
        self.display()
        image = self.get_selected_id()
        line = self.line_max + 2
        self.screen.addstr(line, 0, f'are you sure to delete {image.short_id} ({image.tags}) ? (y/n)')
        key = self.screen.getkey()
        if key == 'y':
            self.client.images.remove(image.id)
            self.images.pop(image.id, None)
            self.line_max = max(self.line_max - 1, 0)
        self.screen.addstr(line + 1, 0, ' ' * self.w)

    def setup(self):
        """List availables images and reset the current line selection to 0
        """
        self.line = 0
        self.images = {}
        for img in self.client.images.list():
            self.images[img.id] = img
        self.line_max = max(len(self.images) - 1, 0)

    def display(self):
        line = 0
        total = 0
        for img in self.images.values():
            color = curses.A_UNDERLINE if self.line == line else curses.A_DIM
            size_bytes = img.attrs.get('Size')
            size = wsize(size_bytes)
            tag = img.tags[0] if len(img.tags) else 'None'
            self.screen.addstr(line, 1, f'{size:10} {tag:42} {img.short_id}', color)
            line += 1
            total += size_bytes
        self.screen.addstr(line, 1, '-' * 80)
        line += 1
        self.screen.addstr(line, 1, wsize(total))


if __name__ == "__main__":
    m = DockerImagesManager()
    # m = MainWindow('Docker Images Manager')
    # w.close()
    # print(m.x, m.y, m.w, m.h)
    m.loop()
