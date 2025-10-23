from logging import getLogger
from locale import strxfrm
from typing import ClassVar, Iterator

logger = getLogger(__name__)


class Tags:
    """
    Helper class that manages tags.

    :param tags: tags sorted by category
    """

    _TAGS: ClassVar["Tags"]
    _tag_map_ids: dict[tuple[str, str], int]

    @classmethod
    def validate(cls, list_of_tags: str) -> "Tags":
        """
        Converts a string of comma separated words into a valid Tags instance.

        The string is split after each comma. If the words in the resulting list are
        valid tags, they will be sorted by category.

        :param list_of_tags: string of comma separated words
        :returns: a Tags instance with only valid sorted tags
        """
        if not list_of_tags:
            return cls({})

        tmp: dict[str, set[str]] = dict()
        for tag in list_of_tags.split(","):
            if tag := tag.strip():
                valid = False
                for category, tags in cls.TAGS():
                    if tag in tags:
                        valid = True
                        try:
                            tmp[category].add(tag)
                        except KeyError:
                            tmp[category] = {tag}
                if not valid:
                    logger.warning(f"Invalid tag {tag}")

        return cls(tmp)

    @classmethod
    def TAGS(cls, force_reload: bool = False) -> "Tags":
        """
        Contains all available tags.

        If the class doesn't have an attribute "_TAGS" or if `force_reload` is True,
        the Tags are loaded from the SQL database.

        :param force_reload: reload the tags from the SQL database.
        :returns: all available tags
        """
        if not hasattr(cls, "_TAGS") or force_reload:
            from sqlalchemy.sql.expression import select

            from phystool.physql import physql_db
            from phystool.physql.models import Tag, Category

            data: dict[str, set[str]] = {}
            cls._tag_map_ids = {}
            with physql_db() as session:
                for tag_id, tag_name, category_name in session.execute(
                    select(Tag.id, Tag.name, Category.name)
                    .join(Tag, Category.tag_set)
                    .order_by(Category.name, Tag.name)
                ):
                    if category_name in data:
                        data[category_name].add(tag_name)
                    else:
                        data[category_name] = {tag_name}
                    cls._tag_map_ids[(category_name, tag_name)] = tag_id
            cls._TAGS = Tags(data)
        return cls._TAGS

    @classmethod
    def create_new_tag(cls, category_name: str, tag_name: str) -> None:
        """
        Create a new tag

        :param category_name: name of the category's tag
        :param tag_name: name of the tag
        """
        from sqlalchemy.sql.expression import select

        from phystool.physql import physql_db
        from phystool.physql.models import Tag, Category

        if tags := cls._TAGS[category_name]:
            tags.append(tag_name)
            tags.sort(key=strxfrm)
        else:
            cls._TAGS.data[category_name] = [tag_name]

        with physql_db() as session:
            if not (
                category := session.scalars(
                    select(Category).filter_by(name=category_name)
                ).one_or_none()
            ):
                category = Category(name=category_name)
                session.add(category)

            session.add(Tag(name="tag", category=category))

    @classmethod
    def from_ids(cls, pks: list[int]) -> "Tags":
        from sqlalchemy.sql.expression import select

        from phystool.physql import physql_db
        from phystool.physql.models import Category, Tag

        data: dict[str, set[str]] = {}
        with physql_db() as session:
            for category_name, tag_name in session.execute(
                select(Category.name, Tag.name).join(Category).filter(Tag.id.in_(pks))
            ):
                if category_name in data:
                    data[category_name].add(tag_name)
                else:
                    data[category_name] = {tag_name}
        return Tags(data)

    def __init__(self, tags: dict[str, set[str]]):
        self.data = {
            category: sorted(tags, key=strxfrm)
            for category, tags in tags.items()
            if tags  # NOTE: category should't be an empty list
        }

    def __getitem__(self, key) -> list[str]:
        return self.data.get(key, [])

    def __iter__(self) -> Iterator[tuple[str, list[str]]]:
        for category, tags in self.data.items():
            yield category, tags

    def __add__(self, other: "Tags") -> "Tags":
        # NOTE: use an empty Tag to avoid redundant sort in __init__
        out = Tags({})
        out.data = self.data.copy()
        out += other
        return out

    def __iadd__(self, other: "Tags") -> "Tags":
        self.data = {
            category: sorted(tags, key=strxfrm)
            for category in sorted(self.data.keys() | other.data.keys())
            if (tags := set(self[category] + other[category]))
        }
        return self

    def __sub__(self, other: "Tags") -> "Tags":
        # NOTE: use an empty Tag to avoid redundant sort in __init__
        out = Tags({})
        out.data = self.data.copy()
        out -= other
        return out

    def __isub__(self, other: "Tags") -> "Tags":
        self.data = {
            category: sorted(tags, key=strxfrm)
            for category in sorted(self.data.keys() | other.data.keys())
            if (tags := set(self[category]) - set(other[category]))
        }
        return self

    def __bool__(self) -> bool:
        for tags in self.data.values():
            if tags:
                return True
        return False

    def __str__(self) -> str:
        return ", ".join([tag for tags in self.data.values() for tag in tags])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tags):
            return False

        if len(self.data.keys()) != len(other.data.keys()):
            return False

        for category, tags in self:
            if set(other[category]) != set(tags):
                return False
        return True

    def list_tags(self) -> None:
        """Prints each tag on a different line."""
        for tags in self.data.values():
            for tag in tags:
                print(tag)

    def as_ids(self) -> set[int]:
        return {
            self._tag_map_ids[(category, tag)]
            for category, tags in self.data.items()
            for tag in tags
        }

    def with_overlap(self, other: "Tags") -> bool:
        """
        Returns `False` if a category doesn't share any tag between this instance and
        the other instance, otherwise, returns `True`

        :warning: Returns `False` if, for any category, either set or the two sets are
            empty (should not happen in the code).
        """
        if other:
            for category in other.data.keys():
                if set(self[category]).isdisjoint(other[category]):
                    return False
        return True

    def without_overlap(self, other: "Tags") -> bool:
        """
        Returns `False` if a category shares at least one tag between this instance and
        the other instance, otherwise, returns `True`

        :warning: Doesn't necessarily return `True` if, for a given category, either set
            or the two sets are empty (should not happen in the code).
        """
        if other:
            for category in other.data.keys():
                if not set(self[category]).isdisjoint(other[category]):
                    return False
        return True
