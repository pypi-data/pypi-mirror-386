import sys
from .fetcher import list_algorithms, get_algorithm

def main():
    if len(sys.argv) < 2:
        print("Usage: algoinc <command> [algorithm]")
        print("Commands: list, get <algorithm>")
        return

    command = sys.argv[1]

    if command == "list":
        list_algorithms()
    elif command == "get":
        if len(sys.argv) < 3:
            print("Usage: algoinc get <algorithm>")
        else:
            get_algorithm(sys.argv[2])
    else:
        print("Unknown command:", command)
