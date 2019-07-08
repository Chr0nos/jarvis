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


class Main:
    def __init__(self):
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(True)

    def __del__(self):
        curses.nocbreak()
        self.screen.keypad(False)
        curses.echo()
        curses.endwin()

    def refresh(self, key):
        self.screen.addstr(2, 10, f'hello world, {key}')

    def loop(self):
        key = None
        while True:
            self.screen.clear()
            self.refresh(key)
            self.screen.refresh()
            key = self.screen.getkey()
            #key = self.screen.gethc()


class CursesErrorHandler:
    def loop_handler(self):
        while True:
            try:
                self.loop()
            except KeyboardInterrupt:
                return
            except Exception as err:
                self.screen.clear()
                self.screen.addstr(10, 10, 'error: ' + str(err))
                self.screen.refresh()
                self.screen.getch()



class DockerImagesManager(Main, CursesErrorHandler):
    def __init__(self):
        super().__init__()
        self.line_max = 0
        self.client = docker.from_env()
        self.setup()

    def action(self, key):
        self.screen.addstr(42, 0, f'action: {key} {type(key)}')
        if key == 'd':
            self.delete_selection()
        if key == 'KEY_UP':
            self.line = max(self.line - 1, 0)
        if key == 'KEY_DOWN':
            self.line = min(self.line + 1, self.line_max)

    def get_selected_id(self):
        return list(self.images.values())[self.line]

    def delete_selection(self):
        image = self.get_selected_id()
        self.screen.addstr(44, 0, f'are you sure to delete {image.short_id} ({image.tags}) ? (y/n)')
        key = self.screen.getkey()
        if key == 'y':
            self.client.images.remove(image.id)
            self.images.pop(image.id, None)
        self.screen.addstr(44, 0, ' ' * 80)

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

    def refresh(self, key):
        if key == 'q':
            raise KeyboardInterrupt
        if key == 'r':
            self.setup()
        self.action(key)
        self.display()


if __name__ == "__main__":
    m = DockerImagesManager()
    m.loop_handler()
