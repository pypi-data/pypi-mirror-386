
from argparse import ArgumentParser, Namespace
from typing import List, Optional, TypedDict


class CommitFlag(TypedDict):
    generate: Optional[int]
    excludeFiles: List[str]
    stageAll: bool
    commitType: Optional[str]
    directory: bool
    rawArgv: List[str]


# Function to parse command-line arguments
def parse_arguments() -> CommitFlag:
    parser = ArgumentParser(
        description="Commit your changes with AI-generated messages.",
        allow_abbrev=False
    )
    parser.add_argument(
        "--generate",
        "-g",
        type=int,
        default=None,
        help="Number of commit messages to generate",
    )
    parser.add_argument(
        "--excludeFiles",
        "-e",
        nargs="*",
        default=[],
        help="Files to exclude from the diff",
    )
    parser.add_argument(
        "--stageAll", "-s", action="store_true", help="Stage all changes"
    )
    parser.add_argument(
        "--commitType", "-t", type=str, default=None, help="Type of commit"
    )
    parser.add_argument(
        "--directory", "-d", action="store_true", 
        help="Generate separate commits per root directory"
    )
    parser.add_argument(
        "rawArgv", nargs="*", help="Additional arguments for git commit"
    )

    args: Namespace = parser.parse_args()

    return CommitFlag(
        generate=args.generate,
        excludeFiles=args.excludeFiles,
        stageAll=args.stageAll,
        commitType=args.commitType,
        directory=args.directory,
        rawArgv=args.rawArgv,
    )
