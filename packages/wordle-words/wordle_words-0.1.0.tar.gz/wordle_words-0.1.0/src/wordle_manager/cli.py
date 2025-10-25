import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        prog="wordle-manager",
        description="Examine and modify the Wordle word list",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="action", required=False)
    subparsers.add_parser("stats", help="Show statistics")
    subparsers.add_parser("dedup", help="Remove duplicates")
    subparsers.add_parser("sort", help="Sort the list")
    subparsers.add_parser("clean", help="Remove invalid words")

    find_parser = subparsers.add_parser("find-scarce", help="Find scarce letters")
    find_parser.add_argument("--num", type=int, default=3)

    add_parser = subparsers.add_parser("add", help="Add a word")
    add_parser.add_argument("word", help="Word to add")
    args = parser.parse_args()
    return args
