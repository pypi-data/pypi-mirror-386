import os

def get_extension(path):
    return os.path.splitext(path)[1].lower()
