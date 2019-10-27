from datetime import datetime, timedelta


class SpeedOMetter:
    """Provides a easy way to monitor speed of a download
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.last_size = 0
        self.last_date = datetime.now().timestamp()

    def update(self, new_size) -> int:
        """return the bytes per seconds since last upadte.
        """
        now = datetime.now().timestamp()
        delta_time = now - self.last_date
        delta_size = new_size - self.last_size

        self.last_date = now
        self.last_size = new_size
        try:
            return int(delta_size / delta_time)
        except ZeroDivisionError:
            return 0


def eta(size, speed) -> timedelta:
    """size in bytes,
    speed in bytes per second
    """
    try:
        return timedelta(seconds=size / speed)
    except ZeroDivisionError:
        return timedelta(seconds=0)
