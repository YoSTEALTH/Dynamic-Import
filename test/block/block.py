__all__ = '__block__',  # this should raise ValueError since its mimicking magic method


def __block__():  # conflict
    return 'inside __block__()'
