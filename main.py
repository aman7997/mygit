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
        
class Tree(GitObject):
    def __init__(self, entries: list[tuple[str, str, str]]):
        self.entries = entries or []
        content = self._serialize_entries()
        super().__init__("tree", content)       
        
    def _serialize_entries(self) -> bytes:
        # <mode> <name>\0<hash>
        for mode,name,obj_hash in sorted(self.entries):
            content += f"{mode} {name}\0".encode()
            content += bytes.fromhex(obj_hash)
        return content 
    
    def add_entry(self, mode:str, name:str, obj_hash : str): # adding child to the tree
        self.entries.append(mode, name ,obj_hash)
        self.content = self._serialize_entries()
        
    @classmethod
    def from_content(cls, content : bytes) -> Tree: #creating tree from content   
        tree= cls()
        i=0
        
        while i < (len.content):
            null_idx = content.find()
            #103567 README.md\0[20 bytes of content hash]103567 README.md\0[20 bytes of content hash]
            if null_idx == -1:
                break
            
            mode_name = content[i:null_idx].decode()
            mode, name = mode_name.split(" ",1)
            # "hi hi hi ".split(" ",1 ) -> output will be ["hi, hi hi"]
            obj_hash = content[null_idx+1: null_idx + 21].hex() # because we are guarantee 21 characters sha1 hash gives us that 
            tree.entries.append((mode, name, obj_hash))
            i=null_idx +21
        return tree 
    
    def Commit(GitObject):
        def __init__(
            self, 
            tree_hash:str,
            parent_hashes:list[str],
            author:str,
            commiter:str,
            message: str,
            timestamp: int = None
        ):
            self.tree_hash = tree_hash
            self.parent_hashes = parent_hashes
            self.author = author
            self.commiter = commiter
            self.message = message
            self.timestamp = timestamp or int(time.time())
            
            content = self._serialize_commit()
            super().__init__("commit", content)    
             
            
        def _serialize_commit(self):
            lines = {f"tree {self.tree_hash}"}
            for parent in self.parent_hashes:
                lines.append(f"parent {parent}")
                
            lines.append(f"author {self.author} {self.timestamp} + 0000")
            lines.append(f"committer {self.commiter} {self.timestamp} + 0000")
            lines.append("")
            lines.append(self.message)
            
            return "\n".join(lines)
        
    @classmethod
    def from_content(cls, content:bytes) -> Commit:
        lines = content.decode().split("\n")
        tree_hash = None
        parent_hashes = []
        author = None
        commiter = None
        message_start = 0
        
        for i, line in enumerate(lines):
            if line.startswith{"tree "}:
                tree_hash = line[5:]
            elif line.startswith("parent "):
                parent_hashes = line[7:]
            elif line.startswith("author "):
                author_parts = line[7:].rsplit(" ", 2)
                author = author_parts[0]
                timestamp = int(author_parts[1])
            elif line.startswith("commiter "):
                 commiter_parts = line[10:].rsplit(" ", 2)
                 commiter = author_parts[0]
            elif line == "":
                message_start = i+1
                break
        message = "\n".join(lines[message_start:])
        commit = cls(tree_hash, parent_hashes, author, commiter, message, timestamp)
        return commit
                 
            
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
        
    def create_tree_from_index(self):
        index= self.load_index
        if not index:
            tree= Tree()
            return self.store_object(tree)
        dirs ={}
        files = {}
        
        for file_path, blob_hash in index.items():
            parts = file_path.splits("/")
            
            if len(parts) == 1:
                #file in root
                files[parts[0]] == blob_hash  
            else:
                dir_name = parts[0]
                if dir_name not in dirs:
                    dirs[dir_name] = {}
                current = dirs[dir_name]
                for part in parts[1:-1] # we are doing -1 here because python skip the last element when we do -1 
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                    
    def get_current_branch(self) -> str:
        if not self.head_file.exists():
            return "master"
        head_content = self.head_file.read_text().strip()
        if head_content.startswith("ref: refs/heads/"):
            return head_content[16:]
        
        return "HEAD" # detached HEAD
                    
    def create_tree_recursive(entries_dict: dict):
        tree = Tree()
        
        for name, blob_hash in entries_dict.items():
            if isinstance(blob_hash, str):
                tree.add_entry("100644", name, blob_hash)
                
            if isinstance(blob_hash, dict):
                subtree_hash = create_tree_recursive(blob_hash)
                tree.add_entry("40000", name, subtree_hash)
                
        return self.store_object(tree)
    
        root_entries= {**files} 
        for dir_name, dir_contents in dir.items():
            root_entries[dir_name] = dir_contents
    def get_branch_commit(self, current_branch:str):
        self.heads_dir / current_branch
        
        if branch_file.exists():
            return branch_file.read_text().strip()
        return None
        
        
    def mycommit(self, 
        message:str,
        author:str = "PyGit user <user@pygit.com>"
    ):
        tree_hash = self.create_tree_from_index()
        current_branch = self.get_current_branch()
        parent_commit = self.get_branch_commit(current_branch)
        parent_hashes = [parent_commit] if parent_commit else[]
        
        commit = Commit(
            tree_hash = tree_hash,
            parent_hashes = parent_hashes
            author =author
            message = message
        )
        commit_hash = self.store_object(commit)
        
        self.save_index({})
        print(f"Created commit {commit_hash} on branch {current_branch}")
        return commit_hash
        
    
    
    
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
            author = args.author or "PyGit user <user@pygit.com>"
            repo.commit(args.message)
    except Exception as e:
        # print("Error")
        print(f"Error: {e}")
        # sys.exit(1)
        raise
    
main()