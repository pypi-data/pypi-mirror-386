"""cobib-zotero's configuration."""

import logging
from dataclasses import dataclass, field

from cobib.config.config import _ConfigBase
from typing_extensions import override

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


@dataclass
class ZoteroPluginConfig(_ConfigBase):
    """The configuration of the `cobib_zotero` plugin."""

    field_map: dict[str, str | None] = field(
        default_factory=lambda: {
            # mapped fields
            "publicationTitle": "journal",
            # trivial fields
            "DOI": "doi",
            "ISSN": "issn",
            "issue": "issue",
            "pages": "pages",
            "series": "series",
            "title": "title",
            "url": "url",
            "volume": "volume",
            # skipped fields
            "key": None,
            "shortTitle": None,
            "version": None,
        }
    )
    """A mapping of Zotero's field names to coBib's field names.

    When a field name maps to `None`, this means it will skip it without warning about its presence.
    """

    @override
    def validate(self) -> None:
        LOGGER.info("Validating the runtime configuration.")
        self._assert(
            isinstance(self.field_map, dict), "zotero_plugin_config.field_map should be a dict."
        )


zotero_plugin_config = ZoteroPluginConfig()
"""This is the runtime configuration object. It is exposed on the module level via:
```python
from cobib_zotero.config import zotero_plugin_config
```
"""
zotero_plugin_config.defaults()
