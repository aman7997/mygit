import argparse
from pathlib import Path
import sys
import json


class Repository:
    def __init__(self, path = "."):
        self.path = Path(path).resolve()
        self.git_dir = self.path / ".pygit"
        
        #.pygit/objects
        self.objects_dir = self.path / "objects"
        
        #/.pygit/refs
        self.refs_dir = self.path / "refs"
        self.heads_dir = self.refs_dir / "heads"
        
        #HEAD file
        self.head_file = self.path / "HEAD"
        
        #/.pygit/index
        self.index_file = self.path / "index"
        
    def myinit(self) -> bool:
        
        if self.git_dir.exists():
            return False
        
        #create directories
        self.git_dir.mkdir()
        self.objects_dir.mkdir()
        self.refs_dir.mkdir()
        self.heads_dir.mkdir()
        
        #create initial HEAD pointing to a branch 
        self.head_file.write_text("ref: refs/heads/main\n")
        
        self.index_file.write_text(json.dumps({}, indent=2))
        
        print("Initialzed empty mygit repository in {self.git_dir}")
        
        return True
    


def main():
    parser = argparse.ArgumentParser(
        description = "mygit - A git clone made from scratch"
    )
    
    subparser = parser.add_subparsers(
        dest = "command",
        help = "Available Commands"
    )
    
    #init command 
    init_parser = subparser.add_parser("myinit", help="Initialize a new repository")
    args = parser.parse_args()
    print(args)
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "myinit":
            repo = Repository()
            if not repo.myinit():
                print("Repository already exists")
                return
    except Exception as e:
        print("Error")
        sys.exit(1)
    
main()