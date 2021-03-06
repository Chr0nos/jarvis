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
    PREFIX = 0
    SUFIX = 1
    CLOSE = 42

    def __init__(self, parent, title: str, x: int, y: int, w: int, h: int):
        self.parent = parent
        self.title = title
        self.title_len = len(title)
        self.closed = True
        if parent is None:
            self.x = x
            self.y = y
            self.level = 0
        else:
            self.w = w
            self.h = h
            self.x = x + parent.x
            self.y = y + parent.y
            self.screen = parent.screen
            self.level = parent.level + 1

    def __del__(self):
        self.screen.clear()
        self.refresh_parents()
        self.screen.refresh()

    def __str__(self):
        return f'{self.title} ({self.w}x{self.h})'

    def setAttr(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

    def geometry_auto(self):
        self.x = (self.w >> 2)
        self.y = self.y + 3
        self.w = (self.w >> 1)
        self.h = (self.h >> 1)

    def refresh_parents(self):
        lst = self.parent_list()
        lst.reverse()
        for p in lst:
            p.refresh()

    def parent_iter(self, method, mode, *args, **kwargs):
        def stack_back(parent):
            if parent is None:
                return
            f = getattr(parent, method)
            if mode & self.PREFIX:
                f(*args, **kwargs)
            stack_back(parent.parent)
            if mode & self.SUFIX:
                f(*args, **kwargs)

        stack_back(self.parent)

    def parent_list(self):
        lst = []
        parent = self.parent
        while parent:
            lst.append(parent)
            parent = parent.parent
        return lst

    def put_center(self, y, content: str):
        return self.screen.addstr(
            self.y + y,
            self.x + (self.w >> 1) - (len(content) >> 1),
            content
        )

    def put(self, y, x, *args, **kwargs):
        return self.screen.addstr(self.y + y, self.x + x, *args, **kwargs)

    def decorate(self):
        color = curses.color_pair(3)
        self.put(0, 0, '-' * self.w, color)
        spaces = ' ' * max(self.w - 1, 0)
        for line in range(0, self.h):
            self.put(line, 0, f'|{spaces}|', color)
        self.put(0, 0, '-' * (self.w + 1), color)
        self.put(self.h, 0, '-' * (self.w + 1), color)
        self.put_center(0, str(self))

    def clear(self):
        for line in range(self.h):
            self.put(line, 0, ' ' * self.w)

    def display(self, context=None):
        pass

    def refresh(self):
        self.decorate()
        self.display()
        self.screen.refresh()

    def action(self, key):
        pass

    def onClose(self):
        """Trigger called only if the user pressed 'q' to quit a window.
        """
        pass

    def show(self):
        assert self.screen
        self.closed = False
        while True:
            self.refresh()
            key = self.screen.getkey()
            if key == 'q':
                self.closed = True
                self.onClose()
                return self
            if self.action(key) == self.CLOSE:
                self.closed = True
                return self


class MainWindow(Window):
    def __init__(self, title):
        self.screen = curses.initscr()
        assert self.screen is not None
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        curses.start_color()
        super().__init__(None, title, 0, 0, curses.COLS, curses.LINES)
        self.screen.keypad(True)
        self.color_init()

    def __del__(self):
        self.close()

    def color_init(self):
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    def close(self):
        curses.curs_set(1)
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

    def put(self, y, x, *args, **kwargs):
        color = kwargs.pop('color', None)
        if color is not None:
            return self.screen.addstr(y, x, *args, curses.color_pair(color), **kwargs)
        return self.screen.addstr(y, x, *args, **kwargs)

    def put_center(self, y, content: str):
        return self.screen.addstr(y, (self.w >> 1) - (len(content) >> 1))

    def display(self):
        pass

    def refresh(self):
        self.screen.clear()
        super().refresh()

    def loop_handler(self):
        while True:
            try:
                self.show()
            except KeyboardInterrupt:
                return
            except Exception as err:
                self.screen.clear()
                self.screen.addstr(10, 10, 'error: ' + str(err))
                self.screen.refresh()
                self.screen.getch()


class ConfirmWindow(Window):
    margin = 7

    def __init__(self, parent, title=None, default=False):
        if title is None:
            title = 'Are you sure ?'
        self.state = default
        self.default = default
        w = 60
        h = 10
        x = (parent.w >> 1) - (w >> 1)
        y = (parent.y) + 3
        super().__init__(parent, title, x, y, w, h)

    def action(self, key):
        if key == 'y':
            self.state = True
            return self.CLOSE
        if key == 'n':
            self.state = False
            return self.CLOSE
        if key in ('KEY_LEFT', 'KEY_RIGHT'):
            self.state = not self.state
        if key == '\n':
            return self.CLOSE

    def display(self):
        col = self.w >> 1
        line = self.h >> 1
        self.put(line, col - self.margin, 'Yes', curses.A_UNDERLINE if self.state else curses.A_DIM)
        self.put(line, col + self.margin, 'No', curses.A_UNDERLINE if not self.state else curses.A_DIM)

    def onClose(self):
        self.state = self.default


class DockerImagesManager(MainWindow):
    def __init__(self):
        super().__init__('Docker Images Manager')
        self.line_max = 0
        self.client = docker.from_env()
        self.setup()

    def action_delete(self):
        image = self.get_selected_id()
        if not ConfirmWindow(self, title=f'Delete {image.short_id} ?').show().state:
            return
        self.client.images.remove(image.id, force=True)
        self.images.pop(image.id, None)
        self.line_max = max(self.line_max - 1, 0)
        self.display()

    def action_test_window(self):
        class TestWindow(Window):
            def action(self, key):
                if key == 'w':
                    w = TestWindow(self, 'Test', 2, 2, self.w, self.h)
                    w.selection = self.selection
                    w.show()

                if key == 'd' and ConfirmWindow(self).show().state:
                    raise KeyboardInterrupt

            def display(self):
                self.put_center(1, self.selection.short_id)
                self.put_center(2, str(self.selection.tags))
                self.put_center(3, str(self.level))

        w = TestWindow(self, 'test', (self.w >> 2), self.y + 3, (self.w >> 1), (self.h >> 1))
        w.selection = self.get_selected_id()
        w.show()

    def action_scroll_up(self):
        self.line = max(self.line - 1, 0)

    def action_scroll_down(self):
        self.line = min(self.line + 1, self.line_max)


    def action(self, key):
        self.screen.addstr(curses.LINES - 1, 0, f'action: {key}')
        actions = {
            'd': self.action_delete,
            'w': self.action_test_window,
            'r': self.setup,
            'KEY_UP': self.action_scroll_up,
            'KEY_DOWN': self.action_scroll_down
        }
        if actions.get(key):
            actions[key]()

    def get_selected_id(self):
        return list(self.images.values())[self.line]

    def delete_selection(self):
        image = self.get_selected_id()
        self.client.images.remove(image.id, force=True)
        self.images.pop(image.id, None)
        self.line_max = max(self.line_max - 1, 0)
        self.display()

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
            size_bytes = img.attrs.get('Size')
            size = wsize(size_bytes)
            tag = img.tags[0] if len(img.tags) else 'None'
            self.put(line, 0, f'{size:10} {tag:42} {img.short_id}',
                color=(2 if line == self.line else 1))
            if line + 3 > curses.LINES:
                return
            line += 1
            total += size_bytes
        self.screen.addstr(line, 1, '-' * 80)
        line += 1
        self.screen.addstr(line, 1, wsize(total))


if __name__ == "__main__":
    m = DockerImagesManager()
    m.loop_handler()
