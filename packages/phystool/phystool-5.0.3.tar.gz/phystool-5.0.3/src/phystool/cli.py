from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from logging import getLogger
from pathlib import Path
from uuid import UUID

from phystool.latex import PdfLatex
from phystool.pdbfile import PDBFile
from phystool.tags import Tags

logger = getLogger(__name__)


def _default(args) -> None:
    if args.list_tags:
        Tags.TAGS().list_tags()
    elif args.new_pdb_filename:
        from phystool.config import config

        print(config.new_pdb_filename())
    elif args.consolidate:
        from phystool.physql.metadata import consolidate

        consolidate()
    elif args.about:
        from phystool.physql.metadata import stats
        from json import dumps

        # dumps(...) enforces double rather than single quotes
        print(dumps(stats(), indent=4))
    elif args.git:
        from phystool.physgit import run_git_in_terminal

        run_git_in_terminal()


def _search(args) -> None:
    from phystool.physql.metadata import filter_pdb_files
    from phystool.tags import Tags

    for pdb_file in filter_pdb_files(
        query=args.query,
        uuid_bit=args.uuid,
        pdb_types=args.pdb_types,
        selected_tags=args.tags,
        excluded_tags=Tags({}),
    ):
        print(pdb_file)


def _pdbfile(args) -> None:
    if args.compile:
        pdb_file = PDBFile.from_file(args.uuid)
        pdb_file.compile(True)
    elif args.pytex:
        from phystool.pytex import PyTex

        PyTex(args.uuid)
    elif args.cat:
        from phystool.helper import bat

        bat(args.uuid)
    elif args.zip:
        try:
            pdb_file = PDBFile.from_file(args.uuid)
            pdb_file.zip()
        except FileNotFoundError:
            logger.error(f"PDBFile '{args.uuid}' does not exist")
    elif args.update:
        from phystool.physql.metadata import update_pdb_file

        update_pdb_file(args.uuid)
    elif args.remove:
        from phystool.helper import terminal_yes_no, bat
        from phystool.physql.metadata import remove_pdb_files

        bat(args.uuid)
        if terminal_yes_no("Remove files?"):
            remove_pdb_files([args.uuid])


def _tags(args) -> None:
    from sqlalchemy.sql.expression import select

    from phystool.physql import physql_db
    from phystool.physql.models import PDBRecord

    with physql_db() as session:
        pdb_file = PDBFile.from_record(
            session.scalars(select(PDBRecord).filter_by(uuid=args.uuid)).one()
        )
        pdb_file.update_tags(session, to_remove=args.remove, to_add=args.add)
        if args.list:
            pdb_file.tags.list_tags()
        else:
            print(pdb_file)


def _pdflatex(args) -> None:
    from phystool.latex import LatexLogParser, LogFileMessage, PdfLatex
    from phystool.helper import texfile_to_symlink

    if args.raw_log:
        LogFileMessage.toggle_verbose_mode()

    if not args.filename.exists():
        logger.error(f"'{args.filename}' not found")
    elif args.filename.suffix == ".log" or args.logtex:
        if not args.filename.with_suffix(".log").exists():
            args.filename = texfile_to_symlink(args.filename).with_suffix(".log")
            if not args.filename.exists():
                logger.error(f"'{args.filename}' not found")
                return
        llp = LatexLogParser(args.filename)
        llp.process()
        llp.as_log()
    else:
        pdflatex = PdfLatex(texfile_to_symlink(args.filename))
        if args.output:
            pdflatex.full_compile(args.output, args.can_recompile)
        if args.clean:
            pdflatex.clean([".aux", ".log", ".out", ".toc"])


def _evaluation(args):
    from phystool.evaluation import EvaluationManager

    metadata = EvaluationManager()
    if args.klass_list_current:
        metadata.klass_list()
    elif args.create_for_klass:
        metadata.evaluation_create_for_klass(args.create_for_klass)
    elif args.list_current:
        metadata.evaluation_list()
    elif args.search:
        metadata.evaluation_search(args.search)
    elif args.edit:
        metadata.evaluation_edit(args.edit)
    elif args.update:
        metadata.evaluation_update(args.update)


def get_parser():
    parser = ArgumentParser(
        prog="phystool",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.set_defaults(func=_default)
    parser.add_argument(
        "--list-tags",
        help="Lists all possible tags",
        action="store_true",
    )
    parser.add_argument(
        "--consolidate",
        help="Consolidates the SQL database",
        action="store_true",
    )
    parser.add_argument(
        "--new-pdb-filename",
        help="Returns new PDBFile filename",
        action="store_true",
    )
    parser.add_argument(
        "--git",
        help="Commits database modifications to git",
        action="store_true",
    )
    parser.add_argument(
        "--about",
        help="Prints information about phystool and the database (as json)",
        action="store_true",
    )

    sub_parser = parser.add_subparsers()
    ###########################
    # search
    ###########################
    search_parser = sub_parser.add_parser(
        "search",
        help="Search in database",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    search_parser.set_defaults(func=_search)
    search_parser.add_argument(
        "--tags",
        help="Filter by tags",
        default=Tags({}),
        type=Tags.validate,
    )
    search_parser.add_argument(
        "--pdb-types",
        help="Filter by types",
        default=[],
        type=PDBFile.validate_type,
    )
    search_parser.add_argument(
        "--uuid",
        help="Filter by uuid containing",
        default="",
    )
    search_parser.add_argument(
        "--query",
        help="Filter the search by content matching the query",
        default="",
    )

    ###########################
    # PDBFile
    ###########################
    pdbfile_parser = sub_parser.add_parser(
        "pdbfile",
        help="Act on pdbfile",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    pdbfile_parser.set_defaults(func=_pdbfile)
    pdbfile_parser.add_argument(
        "--cat",
        help="Display in terminal",
        action="store_true",
    )
    pdbfile_parser.add_argument(
        "--compile",
        help="Compile '.tex' file",
        action="store_true",
    )

    pdbfile_parser.add_argument(
        "uuid",
        help="Select the PDBFile by its uuid",
        type=UUID,
    )
    pdbfile_parser.add_argument(
        "--pytex",
        help="Execute Python code",
        action="store_true",
    )
    pdbfile_parser.add_argument(
        "--remove",
        help="Remove from database",
        action="store_true",
    )
    pdbfile_parser.add_argument(
        "--update",
        help="Update metadata by parsing the '.tex' file",
        action="store_true",
    )
    pdbfile_parser.add_argument(
        "--zip",
        help="Zip with its dependencies",
        action="store_true",
    )

    ###########################
    # PDBFile -> Tags
    ###########################
    sub_sub_parser = pdbfile_parser.add_subparsers()
    tags_subparser = sub_sub_parser.add_parser(
        "tags",
        help="List or edit tags for selected PDBFile",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    tags_subparser.set_defaults(func=_tags)
    tags_subparser.add_argument(
        "--add",
        help="Add tags given as a comma separated list",
        type=Tags.validate,
        default=Tags({}),
    )
    tags_subparser.add_argument(
        "--remove",
        help="Remove tags given as a comma separated list",
        type=Tags.validate,
        default=Tags({}),
    )
    tags_subparser.add_argument(
        "--list",
        help="List tags",
        action="store_true",
    )

    ###########################
    # PdfLatex
    ###########################
    pdflatex_parser = sub_parser.add_parser(
        "pdflatex",
        help="Compile LaTeX documents or parse logs",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    pdflatex_parser.set_defaults(func=_pdflatex)
    pdflatex_parser.add_argument(
        "filename",
        help="Path to '.tex' file",
        type=Path,
    )
    pdflatex_parser.add_argument(
        "--output",
        help="Move pdf to destination",
        type=PdfLatex.output,
    )
    pdflatex_parser.add_argument(
        "--logtex",
        help="Dislpay .log file",
        action="store_true",
    )
    pdflatex_parser.add_argument(
        "--can-recompile",
        help="Compile a second time if the log file mentions the need",
        action="store_true",
    )
    pdflatex_parser.add_argument(
        "--raw-log",
        help="Display raw error message",
        action="store_true",
    )
    pdflatex_parser.add_argument(
        "--clean",
        help="Remove auxiliary files",
        action="store_true",
    )

    ###########################
    # evaluation
    ###########################
    evaluation_parser = sub_parser.add_parser(
        "evaluation",
        help="Manage evaluations",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    evaluation_parser.set_defaults(func=_evaluation)
    evaluation_parser.add_argument(
        "--klass-list-current",
        help="List classes of the current year",
        action="store_true",
    )
    evaluation_parser.add_argument(
        "--list-current",
        help="List current evaluations",
        action="store_true",
    )
    evaluation_parser.add_argument(
        "--create-for-klass",
        help="Create new evaluation klass",
    )
    evaluation_parser.add_argument(
        "--edit",
        help="Edit evaluation in extracted json file",
    )
    evaluation_parser.add_argument(
        "--update",
        help="Update evaluation",
    )
    evaluation_parser.add_argument(
        "--search",
        help="Search evaluations using given PDBFile",
    )

    return parser
