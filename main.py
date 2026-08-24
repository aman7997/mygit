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
        header = f"{self.type} {len(self.content)}\0".encode()
        return hashlib.sha1(header + self.content).hexdigest()
    
    def serialize(self) -> bytes:
        header = f"{self.type} {len(self.content)}\0".encode()
        return zlib.compress(header + self.content)
    
    @classmethod
    def deserialize(cls, data:bytes) -> GitObject:
        decompressed = zlib.compress(data)
        null_idx = decompressed.find(b"\0")
        header = decompressed[:null_idx]
        content = decompressed[null_idx+1:]
        
        obj_type, size = header.split(" ")
        
        return cls(obj_type, content)
      
class Blob(GitObject): #it is for the sole purpose of storing file content 
      def __init__(self, content:bytes):
          super().__init__(Blob, content)
          
      def get_content(self) -> bytes:
          return self.content
        
        
    
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
        
        self.save_index({})
        
        print("Initialzed empty mygit repository in {self.git_dir}")
        
        return True
    
    def store_object(self, obj: GitObject) -> str:
        obj_hash = obj.hash()
        obj_dir = self.objects_dir/obj_hash[:2]
        obj_file = obj_dir/obj_hash[2:]
        
        if not obj_file.exists():
            obj_dir.mkdir(exist_ok = True)
            obj_file.write_bytes(obj.serialize())
            
        return obj_hash
    
    def load_index(self) -> dict[str, str]:
        if not self.index_file.exists():
            return {}
        
        try:
            return json.loads(self.index_file.read_text())
        except:
            return 
        
    def save_index(self , index: dict[str,str]):
        self.index_file.write_text(json.dumps(index, indent=2))
     
    def add_file(self, path:str):
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        # Read the file content
        content  = full_path.read_bytes()
        # Create BLOB(Binary Large Object) Object from the content
        blob = Blob(content)
        # store the BLOB Object in the database (.pygit/objects)
        blob_hash = self.store_object(blob)
        # Update index to include the file
        index = self.load_index()
        index[path] = blob_hash
        self.save_index(index)
        print(f"Added {path}")
        
    def add_directory(self, path:str):
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Directory {path} not found")
        if not full_path.is_dir():
            raise ValueError(f"{path} is not directory")
        index = self.load_index()
        added_count =0
        #recursively traverse the directory
        for file_path in full_path.rglob("*"):
            if file_path.is_file():
                if ".pygit" in file_path.parts:
                    continue
                content = file_path.read_bytes()
            #create blob objects for all files
            #store all blobs in the object database (.pygit/objects)
                blob = Blob(content)
                blob_hash= self.store_object(blob)
            #update index
                rel_path = str(file_path.relative_to(self.path))    
                index[rel_path] = blob_hash
                added_count+=1
        if added_count > 0:
            print(f"Added {added_count} files from directories {path}")
        else:
            print("The directory path already upto date")
            
        self.save_index(index)
            

    
    def add_path(self, path:str) -> None:
        full_path = self.path / path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        
        if full_path.is_file():
            self.add_file(path)
        elif full_path.is_dir():
            self.add_directory(path)
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
    
    #add command
    add_parser = subparser.add_parser("myadd", help="Add files and directories to the staging area")
    add_parser.add_argument("paths", nargs = '+', help = "Files and directories to add")
    
    #commit command
    commit_parser = subparser.add_parser("mycommit", help="Create a New Commit")
    add_parser.add_argument("--msg", help = "Commit Message", required=True)
    add_parser.add_argument("--author", help = "Author name and email")

    
    
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
                
        elif args.command == "mycommit":
            if not repo.git_dir.exists():
                print("Not a git repository")
                return
            
            repo.commit(args.message)
    except Exception as e:
        # print("Error")
        print(f"Error: {e}")
        # sys.exit(1)
        raise
    
main()