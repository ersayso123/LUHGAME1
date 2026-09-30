"""A baller on a roster: name, stats and attributes. Match positions live in match.Actor."""
from dataclasses import dataclass, field

from . import settings as S
from . import attributes


@dataclass
class Player:
    name: str
    number: int
    stats: dict = field(default_factory=lambda: {s: 40 for s in S.STAT_NAMES})
    main_attr: str | None = None
    main_lvl: int = 0
    sec_attr: str | None = None
    sec_lvl: int = 0

    def overall(self):
        avg = sum(self.stats[s] for s in S.STAT_NAMES) / len(S.STAT_NAMES)
        return min(99, round(avg + 2 * self.main_lvl + self.sec_lvl))

    def attr_label(self):
        return attributes.label(self)

    def to_dict(self):
        return {"name": self.name, "number": self.number, "stats": dict(self.stats),
                "main_attr": self.main_attr, "main_lvl": self.main_lvl,
                "sec_attr": self.sec_attr, "sec_lvl": self.sec_lvl}

    @classmethod
    def from_dict(cls, d):
        return cls(name=d["name"], number=d["number"], stats=dict(d["stats"]),
                   main_attr=d.get("main_attr"), main_lvl=d.get("main_lvl", 0),
                   sec_attr=d.get("sec_attr"), sec_lvl=d.get("sec_lvl", 0))

    def copy(self):
        return Player.from_dict(self.to_dict())
