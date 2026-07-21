"""Role assignments model.

Corresponds to "List Role Assignments in a Dataset" endpoint: https://borealisdata.ca/guides/en/latest/api/native-api.html#list-role-assignments-in-a-dataset

"""
# ruff: noqa: N815

from pydantic import BaseModel, ConfigDict


class RoleAssignment(BaseModel):
    """A single role assignment."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    assignee: str | None = None
    roleId: int | None = None
    roleName: str | None = None
    _roleAlias: str | None = None
    definitionPointId: int | None = None

    def get_raw(self, key: str) -> object | None:
        """Get a raw top-level field not covered by the schema (requires extra='allow')."""
        return self.model_extra.get(key) if self.model_extra else None


class RoleAssignments(BaseModel):
    """Role assignments model."""

    model_config = ConfigDict(extra="allow")

    status: str | None = None
    data: list[RoleAssignment] | None = None

    def count_field(self, field_name: str, value: str | int | None = None) -> int:
        """Count the number of occurrences of a field with a specific value. If value is None, counts all occurrences of the field regardless of value.

        Parameters
        ----------
        field_name: The name of the field to count.
        value: The value to look for and count. If None, counts all occurrences of the field regardless of value.

        Returns
        -------
        int: The number of occurrences of the field with the specified value.

        """
        if not self.data:
            return 0

        if value is None:
            return sum(1 for ra in self.data if hasattr(ra, field_name))

        return sum(
            1
            for ra in self.data
            if hasattr(ra, field_name) and getattr(ra, field_name) == value
        )

    def get_value(self, field_name: str) -> list[str | int | None]:
        """Get a list of all values for the given field name. Returns None for role assignments that don't have the field."""
        if not self.data:
            return []
        return [
            getattr(ra, field_name) if hasattr(ra, field_name) else None
            for ra in self.data
        ]


def load_role_assignments(metadata: dict) -> RoleAssignments:
    """Parse a role assignments JSON payload (already loaded as a dict) into a RoleAssignments.

    Accepts either the full `{status, data: {...}}` export envelope, or a bare
    `data`-shaped payload (no envelope), by trying each model in turn.
    """
    if "data" in metadata:
        return RoleAssignments.model_validate(metadata)
    return RoleAssignments(status="OK", data=RoleAssignment.model_validate(metadata))
