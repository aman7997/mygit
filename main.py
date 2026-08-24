from __future__ import annotations
import argparse
from pathlib import Path
import sys
import json
import hashlib
import zlib

class GitObject:
    def __init__(self, obj_type: str, content: bytes):
        self.type = obj_type
        self.content = content
    
    def hash(self) -> str:
        # f(<type> <size>\0<content>)
        header = f"{self.type} {len(self.content)}\0".encode*()
        return hashlib.sha1(header + self.content).hexdigest()
    
    def serialize(self) -> bytes:
        header = f"{self.type} {len(self.content)}\0".encode*()
        return zlib.compress(header + self.content)
    
    @classmethod
    def deserialize(cls, data:bytes) -> GitObject:
        decompressed = zlib.compress(data)
        null_idx = decompressed.find(b"\0")
        header = decompressed[:null_idx]
        content = decompressed[null_idx+1:]
        
        obj_type, size = header.split(" ")
        
        return cls(obj_type, content)
        
        
        
    
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
    
    def add_file(self, path:str):
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        # Read the file content
        content  = full_path.read_bytes()
        # Create BLOB(Binary Large Object) Object from the content
        
        # store the BLOB Object in the database (.git/objects)
        # Update index to include the file
        pass
        
    # def add_directory(self, path:str):
    
    def add_path(self, path:str) -> None:
        full_path = self.path / path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        
        if full_path.is_file():
            self.add_file(path)
        elif full_path.is_dir():
            self.add_directorty(path)
        else:
            raise ValueError(f"{path} is neither a file nor a directory")

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
    add_parser = subparser.add_parser("myadd", help="Add files and directories to the staging area")

    add_parser.add_argument("paths", nargs = '+', help = "Files and directories to add")
    
    args = parser.parse_args()
    print(args)
    
    if not args.command:
        parser.print_help()
        return
    repo = Repository()
    try:
        if args.command == "myinit": 
            if not repo.myinit():
                print("Repository already exists")
                return
        elif args.command == "myadd":
            if not repo.git_dir.exists():
                print("Not a git repository")
                return
            for path in args.paths:
                repo.add_path(path)
    except Exception as e:
        print("Error")
        sys.exit(1)
    
main()