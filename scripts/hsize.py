def hsize(size, factor=1024, precision=2) -> str:
    """Convert a size in bytes to a human readable one
    """
    units = ('b', 'kb', 'Mb', 'Gb', 'Tb', 'Eb', 'Pb', 'Yb')
    p = 0
    mp = len(units) - 1
    while p < mp and size >= factor:
        size /= factor
        p += 1
    return f'{round(size, precision)}{units[p]}'
