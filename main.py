import argparse
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
    
main()