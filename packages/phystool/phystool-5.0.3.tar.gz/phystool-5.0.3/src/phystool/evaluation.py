import datetime
import json

from uuid import uuid4
from pathlib import Path
from logging import getLogger
from phystool.pdbfile import PDBFile
from phystool.config import config

logger = getLogger(__name__)


class Klass:
    def __init__(
        self, uuid: str, name: str, year: int, extra: str, evaluations: list[str]
    ):
        self.uuid = uuid
        self.name = name
        self.year = year
        self.extra = extra
        self.evaluations: list[str] = evaluations

    def __repr__(self) -> str:
        return f"Klass({self.name} [{self.year}/{self.extra}])"

    def __str__(self) -> str:
        return f"{self.name} [{self.year}/{self.extra}]"

    def is_current(self) -> bool:
        return self.year == 2024

    def to_dict(self) -> dict[str, str | list[str] | int]:
        return {
            "name": self.name,
            "year": self.year,
            "extra": self.extra,
            "evaluations": list(self.evaluations),
        }


class Evaluation:
    def __init__(
        self,
        uuid: str,
        klass_uuid: str,
        title: str = "",
        date: str = "2024-08-31",  # FIXME
        number: str = "",
        extra: list[str] = [],
        exercises: list[str] = [],
    ):
        self.uuid: str = uuid
        self.klass_uuid: str = klass_uuid
        self.title: str = title
        self.date: datetime.date = datetime.datetime.fromisoformat(date).date()
        self.number: str = number
        self.extra: list[str] = extra
        self.exercises: list[str] = exercises

    def __lt__(self, other) -> bool:
        return self.date < other.date

    def __repr__(self) -> str:
        out = f"{self.date:%d %b %Y} [{self.number}] {self.title:<30} "
        if self.extra:
            out += ",".join(self.extra)
        return out

    def update(self, data: dict) -> tuple[set[str], set[str]]:
        self.title = data["title"]
        self.date = datetime.datetime.fromisoformat(data["date"]).date()
        self.number = data["number"]
        self.extra = data["extra"]
        old = set(self.exercises)
        new = set(data["exercises"])
        self.exercises = data["exercises"]
        return (old - new), (new - old)

    def to_dict(self) -> dict[str, str | list[str]]:
        return {
            "klass_uuid": self.klass_uuid,
            "title": self.title,
            "date": self.date.isoformat(),
            "number": self.number,
            "extra": self.extra,
            "exercises": self.exercises,
        }


class EvaluationManager:
    EVALUATION_PATH = Path("foo")

    def __init__(self) -> None:
        self._pdb_data: dict[str, PDBFile] = {}
        # exercises_in_evaluation = []
        # for tex_file in config.db.DB_DIR.glob("*.tex"):
        # try:
        # pdb_file = PDBFile(tex_file.stem)
        # exercises_in_evaluation += [
        #     (uuid, pdb_file.uuid) for uuid in pdb_file.evaluations
        # ]
        # except ValueError as e:
        # logger.error(e)
        # logger.error("Ignoring file")

        if self.EVALUATION_PATH.exists():
            with self.EVALUATION_PATH.open() as jsin:
                data = json.load(jsin)
                self._klasses = {
                    uuid: Klass(uuid=uuid, **klass)
                    for uuid, klass in data["klasses"].items()
                }
                self._evaluations = {
                    uuid: Evaluation(uuid=uuid, **evaluation)
                    for uuid, evaluation in data["evaluations"].items()
                }

    def get_klass(self, name: str, year: int) -> Klass:
        for k in self._klasses.values():
            if k.name == name and k.year == year:
                return k
        raise ValueError

    def klass_list(self, current: bool = True) -> None:
        for uuid, klass in self._klasses.items():
            if not current or klass.is_current():
                print(f"{uuid}: {klass.name}")

    def klass_display(self, klass_uuid: str) -> None:
        klass = self._klasses[klass_uuid]
        for uuid in klass.evaluations:
            self.evaluation_display(uuid)

    def evaluation_list(self, current: bool = True) -> None:
        for klass in self._klasses.values():
            if not current or klass.is_current():
                for uuid in klass.evaluations:
                    print(f"{uuid}: {klass.name:<5} {self._evaluations[uuid]}")

    def evaluation_create_for_klass(self, klass_uuid: str) -> str:
        uuid = str(uuid4())
        evaluation = Evaluation(
            uuid=uuid,
            klass_uuid=klass_uuid,
        )
        self._evaluations[uuid] = evaluation
        self._klasses[klass_uuid].evaluations.append(uuid)
        self._save_evaluation(evaluation)
        return uuid

    def evaluation_edit(self, evaluation_uuid: str) -> None:
        fname = Path(f"/tmp/{evaluation_uuid}.json")
        with fname.open("w") as jsout:
            json.dump(
                self._evaluations[evaluation_uuid].to_dict(),
                jsout,
                indent=4,
                ensure_ascii=False,
            )

    def evaluation_update(self, evaluation_uuid: str) -> None:
        try:
            evaluation = self._evaluations[evaluation_uuid]
        except KeyError:
            logger.error(f"Evaluation with {evaluation_uuid} not found")
            return

        fname = Path(f"/tmp/{evaluation_uuid}.json")
        with fname.open() as jsin:
            data = json.load(jsin)

        to_del, to_add = evaluation.update(data)
        for uuid in to_del:
            # self._pdb_data[uuid].evaluations.remove(evaluation_uuid)
            self._pdb_data[uuid].save()
        for uuid in to_add:
            # self._pdb_data[uuid].evaluations.add(evaluation_uuid)
            self._pdb_data[uuid].save()

        self._save_evaluation(evaluation)

    def evaluation_display(self, evaluation_uuid: str) -> None:
        evaluation = self._evaluations[evaluation_uuid]
        print(f"{evaluation} -> {self._klasses[evaluation.klass_uuid]}")
        for uuid in evaluation.exercises:
            print(f"\t{self._pdb_data[uuid]}")

    def evaluation_search(self, uuid: str) -> None:
        pass
        # try:
        # for evaluation_uuid in self._pdb_data[uuid].evaluations:
        # self.evaluation_display(evaluation_uuid)
        # except KeyError:
        # logger.error(f"PDBFile not found ({uuid})")

    def _save_evaluation(self, evaluation: Evaluation) -> None:
        with self.EVALUATION_PATH.open() as jsin:
            data = json.load(jsin)

        data["evaluations"][evaluation.uuid] = evaluation.to_dict()
        data["evaluations"] = {
            uuid: evaluation
            for uuid, evaluation in sorted(
                data["evaluations"].items(), key=lambda x: self._evaluations[x[0]]
            )
        }
        data["klasses"][evaluation.klass_uuid]["evaluations"].append(evaluation.uuid)

        for klass in data["klasses"].values():
            klass["evaluations"] = sorted(
                set(klass["evaluations"]), key=lambda x: self._evaluations[x]
            )

        with self.EVALUATION_PATH.open("w") as jsout:
            json.dump(data, jsout, indent=4, ensure_ascii=False)
