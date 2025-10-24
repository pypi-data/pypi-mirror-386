from logging import getLogger
from typing import Iterator, Sequence
from uuid import UUID

from sqlalchemy.orm.strategy_options import joinedload, selectinload
from sqlalchemy.types import String
from sqlalchemy.sql.expression import delete, func, select

from phystool.config import config
from phystool.helper import greptex, progress_bar
from phystool.pdbfile import PDBFile
from phystool.physql import physql_db
from phystool.physql.models import PDBRecord, PDBType, Category, Tag
from phystool.tags import Tags
from phystool.__version__ import __version__

logger = getLogger(__name__)


def stats() -> dict[str, str | int | Sequence[str] | dict[str, list[str]]]:
    with physql_db() as session:
        return {
            "path": str(config.db.DB_DIR),
            "records_number": session.scalar(func.count(PDBRecord.id)),
            "valid_types": session.scalars(select(PDBType.name)).all(),
            "valid_tags": Tags.TAGS().data,
            "version": str(__version__),
        }


def consolidate() -> None:
    """
    Wrapper function around `create_sql_database()' that prints a minimalistic
    progress bar in the terminal
    """
    _message = ""
    for i, n, message in create_sql_database():
        if _message != message:
            _message = message
            print()
        progress_bar(n, i, 20, f"{message:<30} |")
    print()


def create_sql_database() -> Iterator[tuple[int, int, str]]:
    """Create the SQL database by analysing all '.tex' and related '.json' files"""
    physql_db.remove()
    physql_db.create_tables()

    pdb_type_map = {
        name: PDBType(name=name, standalone=standalone)
        for name, (_, standalone) in config.db.PDB_TYPES.items()
    }

    tags = Tags({})
    tag_map: dict[tuple[str, str], Tag] = {}
    category_map: dict[str, Category] = {}
    pdb_records: list[PDBRecord] = []
    reference_map: dict[UUID, list[UUID]] = {}

    i = 0
    tex_files = list(config.db.DB_DIR.glob("*.tex"))
    n = len(tex_files) - 1
    for i, tex_file in enumerate(tex_files):
        yield i, n, "Updating '.json' and '.pdf' files"
        try:
            pdb_file = PDBFile.from_file(tex_file)
        except ValueError as e:
            logger.error(e)
            continue
        pdb_file.compile(False)
        pdb_file.save()

        tag_set: set[Tag] = set()
        if not pdb_file.tags:
            logger.warning(f"{pdb_file!r} is untagged")
        else:
            tags += pdb_file.tags
            for category_name, pdbfile_tags in pdb_file.tags:
                if not (category := category_map.get(category_name, None)):
                    category = Category(name=category_name)
                    category_map[category_name] = category

                for tag_name in pdbfile_tags:
                    if not (tag := tag_map.get((category_name, tag_name), None)):
                        tag = Tag(name=tag_name, category=category)
                        tag_map[(category_name, tag_name)] = tag
                    tag_set.add(tag)

        pdb_records.append(
            PDBRecord(
                uuid=pdb_file.uuid,
                title=pdb_file.title,
                pdb_type=pdb_type_map[pdb_file.pdb_type],
                tag_set=tag_set,
            )
        )
        if refs := pdb_file.references:
            reference_map[pdb_file.uuid] = refs

    yield 0, 0, "Creating SQL database"
    with physql_db() as session:
        session.add_all(category_map.values())
        session.add_all(tag_map.values())
        session.add_all(pdb_type_map.values())
        session.add_all(pdb_records)

    # Manage references and inherited tags
    with physql_db() as session:
        pdb_record_map = {
            pdb_record.uuid: pdb_record
            for pdb_record in session.scalars(select(PDBRecord))
        }
        for pdb_record_uuid, reference_uuids in reference_map.items():
            tmp_record = pdb_record_map[pdb_record_uuid]
            tmp_record.using_set = {
                pdb_record_map[reference_uuid] for reference_uuid in reference_uuids
            }
            for reference_uuid in reference_uuids:
                pdb_record_map[reference_uuid].tag_set.update(tmp_record.tag_set)

    if tags != Tags.TAGS(force_reload=True):
        physql_db.remove()
        yield 1, 1, "SQL creation failed"
        raise ValueError(f"SQL creation failed")

    yield 0, 0, "Removing extraneous files"
    for f in config.db.DB_DIR.glob("*"):
        if f.suffix in [".aux", ".log"]:
            f.unlink()
        elif (
            f.suffix in [".json", ".pdf", ".pty"]
            and not f.with_suffix(".tex").is_file()
        ):
            logger.info(f"rm {f}")

    yield 1, 1, "Consolidation completed"


def filter_pdb_files(
    query: str,
    uuid_bit: str,
    pdb_types: list[str],
    selected_tags: Tags,
    excluded_tags: Tags,
) -> list[PDBFile]:
    """
    Returns a list of PDBFile that match search criteria

    :param query: string that should appear in the '.tex' file
    :param uuid_bit: string that should match part of a uuid
    :param pdb_type_set: restrain search only to those file types
    :param selected_tags: restrain search to the PDBFiles tagged with any of the
        selected_tags
    :param excluded_tags: exclude PDBFiles tagged with any of the
        excluded_tags
    """
    qs = (
        select(PDBRecord)
        .options(joinedload(PDBRecord.pdb_type))
        .options(selectinload(PDBRecord.tag_set))
        .options(selectinload(PDBRecord.using_set))
    )
    if query:
        qs = qs.filter(PDBRecord.uuid.in_(greptex(query, config.db.DB_DIR, False)))
    if pdb_types:
        qs = qs.filter(PDBType.name.in_(pdb_types)).join(PDBType)
    if uuid_bit:
        qs = qs.filter(func.cast(PDBRecord.uuid, String).like(f"%{uuid_bit}%"))
    with physql_db() as session:
        return [
            PDBFile.from_record(tmp)
            for tmp in sorted(
                [
                    pdb_record
                    for pdb_record in session.scalars(qs)
                    if (
                        pdb_record.tags.with_overlap(selected_tags)
                        and pdb_record.tags.without_overlap(excluded_tags)
                    )
                ],
                reverse=True,
            )
        ]


def update_pdb_file(uuid: UUID) -> None:
    try:
        pdb_file = PDBFile.from_file(uuid)
    except ValueError as e:
        logger.error(e)
        return

    pdb_file.save()
    with physql_db() as session:
        pdb_type = session.execute(
            select(PDBType).filter_by(name=pdb_file.pdb_type)
        ).scalar_one()
        using = session.scalars(
            select(PDBRecord).filter(PDBRecord.uuid.in_(pdb_file.references))
        )
        if pdb_record := session.execute(
            select(PDBRecord).filter_by(uuid=pdb_file.uuid)
        ).scalar():
            pdb_record.title = pdb_file.title
            pdb_record.pdb_type = pdb_type
            pdb_record.using_set = set(using)
            logger.info(f"Successfully updated {pdb_file!r}")
        else:
            session.add(
                PDBRecord(
                    uuid=pdb_file.uuid,
                    title=pdb_file.title,
                    pdb_type=pdb_type,
                    using_set=set(using),
                )
            )
            logger.info(f"Successfully created {pdb_file!r}")


def remove_pdb_files(uuids: list[UUID]) -> None:
    """
    Remove all files related to the PDBFiles. If the database is managed by
    git, the files can be recovered. The PDBRecords are also deleted.
    """
    with physql_db() as session:
        session.execute(delete(PDBRecord).filter(PDBRecord.uuid.in_(uuids)))

    for uuid in uuids:
        for fname in config.db.DB_DIR.glob(f"{uuid}*"):
            logger.info(f"Removing {fname}")
            fname.unlink()
