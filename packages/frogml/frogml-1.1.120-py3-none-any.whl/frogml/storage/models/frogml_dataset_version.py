from frogml.storage.models.frogml_entity_version import FrogMLEntityVersion


class FrogMLDatasetVersion(FrogMLEntityVersion):
    """
    Represent metadata of an uploaded dataset version.

    Inherits:
        FrogMLEntityVersion: Base class for entity versions.
    """

    @classmethod
    def from_entity_version(
        cls, entity_version: FrogMLEntityVersion
    ) -> "FrogMLDatasetVersion":
        return cls(
            entity_name=entity_version.entity_name,
            version=entity_version.version,
            namespace=entity_version.namespace,
            entity_manifest=entity_version.entity_manifest,
        )
