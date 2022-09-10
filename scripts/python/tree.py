"""Generates a string showing a directory hierarchy. 

yoinked from here: https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python
so that my devops scripts have nice output. 
"""
import argparse 
from pathlib import Path

# prefix components:
space =  '    '
branch = '│   '
# pointers:
tee =    '├── '
last =   '└── '


def tree(dir_path: Path, prefix: str=''):
    """A recursive generator, given a directory Path object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters
    """    
    contents = list(dir_path.iterdir())
    # contents each get pointers that are ├── with a final └── :
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, path in zip(pointers, contents):
        yield prefix + pointer + path.name
        if path.is_dir(): # extend the prefix and recurse:
            extension = branch if pointer == tee else space 
            # i.e. space because last, └── , above so no more |
            yield from tree(path, prefix=prefix+extension)

    
if __name__ == "__main__": 
    parser = argparse.ArgumentParser(
        description='Generate a string that shows the file system hierarchy rooted at a directory.'
    )
    parser.add_argument(
        '--path', help='The file path at which to run tree.'
    )
    args = parser.parse_args()
    path = Path(args.path.strip())
    if not path.exists() or not path.is_dir(): 
        raise ValueError(f"Path {path} does not exist or isn't dir.")
    for line in tree(path): 
        print(line)
    