from dataclasses import asdict, dataclass, field
import json

from mkdocs.structure.files import File


@dataclass
class Actor:
    name: str
    handle: str
    summary: str | None = field(default=None)
    icon: str | None = field(default=None)

    def as_json(self):
        return json.dumps(asdict(self))

    def as_file(self, config):
        return File.generated(
            src_uri="fedi-actor.json",
            config=config,
            content=self.as_json(),
        )
