import argparse
import os
from .app import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple Git GUI")
    parser.add_argument('path', nargs='?', default=os.getcwd(), help='Path to git repository')
    args = parser.parse_args()
    run(args.path)


if __name__ == '__main__':
    main()
