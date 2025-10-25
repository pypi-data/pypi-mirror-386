import io
import os
import sys
import argparse
from typing import NoReturn

from .repl import Repl

from .interpreter import Interpreter
from .lexer import *
from .parser import Parser
from .error import *
from . import __version__


def _error(s: str) -> NoReturn:
    error(s)
    exit(1)


def real_main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--debug", action="store_true", help="show debugging information"
    )
    parser.add_argument(
        "--no-run", action="store_true", help="only print the program's AST"
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"beancode version {__version__}"
    )
    parser.add_argument(
        "-i",
        "--stdin",
        action="store_true",
        help="read source from stdin",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-c",
        "--command",
        help="pass a program in as a string",
    )
    group.add_argument("file", nargs="?", type=str)
    args = parser.parse_args()

    if args.no_run:
        args.debug = True
    if args.command is not None:
        file_content = args.command
    elif args.stdin:
        file_content = sys.stdin.read()
    elif args.file is None:
        Repl(args.debug).repl()
        return
    else:
        if not os.path.exists(args.file):
            _error(f"file {args.file} does not exist!")

        try:
            with open(args.file, "r+") as f:
                file_content = f.read()
        except IsADirectoryError:
            _error(f"{args.file} is not a file, but a directory!")
        except Exception as e:
            _error(f"failed to open file {args.file}: {e}")

    lexer = Lexer(file_content)

    try:
        toks = lexer.tokenize()
    except BCError as err:
        err.print(args.file, file_content)
        exit(1)

    if args.debug:
        print("\033[1m=== TOKENS ===\033[0m", file=sys.stderr)
        for tok in toks:
            tok.print(file=sys.stderr)
        print("\033[1m==============\033[0m", file=sys.stderr)

    parser = Parser(toks)

    try:
        program = parser.program()
    except BCError as err:
        err.print(args.file, file_content)
        exit(1)

    if args.debug:
        print("\033[1m=== AST ===\033[0m", file=sys.stderr)
        for stmt in program.stmts:
            print(stmt)
            print()
        print("\033[0m\033[1m=== AST ===\033[0m", file=sys.stderr)

    if args.no_run:
        return

    i = Interpreter(program.stmts)
    i.toplevel = True
    try:
        i.visit_block(None)
    except BCError as err:
        err.print(args.file, file_content)
        exit(1)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    try:
        real_main()
    except KeyboardInterrupt:
        warn("Caught keyboard interrupt")
        exit(1)
    except EOFError:
        warn("Caught EOF")
        exit(1)
    except RecursionError:
        warn("Python recursion depth exceeded! Did you forget your base case?")
    except ValueError:
        warn("Unexpected Python ValueError! Did you work with a very long number?")
    except Exception as e:
        error(
            f'Python exception caught ({type(e)}: "{e}")! Please report this to the developers.'
        )
        raise e


if __name__ == "__main__":
    main()
