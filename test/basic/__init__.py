from dynamic_import import importer


importer(exclude_file='sub/skip-me.py', exclude_dir='skip')


__all__ = 'DEFINE', 're_import'
DEFINE = 123


def re_import():
    pass
