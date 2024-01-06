__all__ = '__block__',  # this should raise ValueError since its mimicking magic method


def __block__():
    return 'inside __block__()'
# conflict
