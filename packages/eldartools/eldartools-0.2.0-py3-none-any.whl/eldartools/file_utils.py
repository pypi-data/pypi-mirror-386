import os

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def file_size(path):
    return os.path.getsize(path)
def read_lines(path):
    with open(path,"r",encoding="utf-8") as f:
        return f.readlines()

def append_file(path, content):
    with open(path,"a",encoding="utf-8") as f:
        f.write(content)

def copy_file(src,dst):
    import shutil
    shutil.copy(src,dst)

def list_files(folder):
    import os
    return [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder,f))]
