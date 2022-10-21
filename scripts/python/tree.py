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


def _tree(dir_path: Path, paths_show, prefix: str=''):
    """A recursive generator, given a directory Path object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters
    """    
    if not any(
        str(p).startswith(str(dir_path)) for p in paths_show
    ):
        # None of the paths to be shown reside within this directory so skip 
        yield None 
    else: 
        sub_dirs = [
            p for p in dir_path.iterdir() if p.is_dir() and any(
                str(pi).startswith(str(p)) for pi in paths_show
            )
        ]
        sub_files = [
            p for p in dir_path.iterdir() if p.is_file() and p in paths_show
        ]
        contents = sub_dirs + sub_files
        # contents each get pointers that are ├── with a final └── :
        pointers = [tee] * (len(contents) - 1) + [last]
        for pointer, path in zip(pointers, contents):
            yield prefix + pointer + path.name
            if path.is_dir(): # extend the prefix and recurse:
                extension = branch if pointer == tee else space 
                # i.e. space because last, └── , above so no more |
                yield from _tree(
                    path, paths_show, prefix=prefix+extension
                )


def tree(dir_path: Path, paths_show):
    for t in _tree(dir_path, paths_show): 
        if t is not None: 
            yield t 


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(
        description='Generate a string that shows the file system hierarchy rooted at a directory.'
    )
    parser.add_argument(
        '--path-dir', help='The path to the directory where tree is rooted'
    )
    parser.add_argument(
        '--paths-show', help=(
            "The subset of file paths to show within the directory structure. "
            "We skip all directories that don't contain one of the files specified "
            "in this list."
        )
    )
    args = parser.parse_args()
    path_dir = Path(args.path_dir.strip()).absolute()
    paths_show = [
        path_dir / Path(p) for p in args.paths_show.split(",")
    ]
    assert path_dir.exists() and path_dir.is_dir()
    assert all(p.exists() for p in paths_show)
    lines = list(tree(path_dir, paths_show))
    for p in paths_show: 
        assert any(l.endswith(str(p.name)) for l in lines)
    for l in lines: 
        print(l)