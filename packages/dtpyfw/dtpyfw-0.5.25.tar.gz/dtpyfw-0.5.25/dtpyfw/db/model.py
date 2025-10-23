"""Base model classes and utilities for SQLAlchemy ORM models.

Provides ModelBase class with common fields, serialization methods, and
helper functions for tracking model changes.
"""

import json
import uuid
from typing import Any, Dict, List

from sqlalchemy import UUID, Column, DateTime, func, inspect
from sqlalchemy.orm import Session

from ..core.jsonable_encoder import jsonable_encoder

__all__ = ("ModelBase",)


def get_difference_between_dictionaries(
    old_value: Any, new_value: Any, path: str = ""
) -> list[str]:
    """Recursively find paths that differ between two dictionary/list
    structures.

    Compares two data structures (dictionaries or lists) and returns a list of
    paths where differences exist. Useful for tracking changes in nested data.

    Args:
        old_value: The original data structure to compare.
        new_value: The new data structure to compare against.
        path: The current path in the structure (used for recursion).

    Returns:
        A list of string paths indicating where changes occurred.
    """
    changes = []

    if isinstance(old_value, dict) and isinstance(new_value, dict):
        # Recursive case for dictionaries
        keys = set(old_value.keys()) | set(new_value.keys())
        for key in keys:
            if key in old_value and key in new_value:
                changes.extend(
                    get_difference_between_dictionaries(
                        old_value[key], new_value[key], f"{path}.{key}" if path else key
                    )
                )
            elif key in old_value:
                changes.append(f"{path}.{key}")
            else:
                changes.append(f"{path}.{key}")
    elif isinstance(old_value, list) and isinstance(new_value, list):
        # Recursive case for lists
        old_items = {json.dumps(item, sort_keys=True): item for item in old_value}
        new_items = {json.dumps(item, sort_keys=True): item for item in new_value}
        old_set, new_set = set(old_items), set(new_items)

        if (old_set - new_set) or (new_set - old_set):
            changes.append(path)

        for item in old_set & new_set:
            old_item = old_items[item]
            new_item = new_items[item]
            if isinstance(old_item, (list, dict)) and old_item != new_item:
                changes.extend(
                    get_difference_between_dictionaries(
                        old_item, new_item, f"{path}[modified]"
                    )
                )
    else:
        # Base case for other types
        if old_value != new_value:
            changes.append(path)

    return changes


def get_modified_keys(instance: Any) -> list[str]:
    """Return the list of attribute keys that have been modified on the
    instance.

    Uses SQLAlchemy's inspection API to detect which attributes have changed
    since the instance was loaded from the database or last committed.

    Args:
        instance: A SQLAlchemy model instance to inspect.

    Returns:
        A list of attribute key names that have been modified.
    """
    inst_state = inspect(instance)
    modified_attrs = [
        attr.key for attr in inst_state.attrs if attr.history.has_changes()
    ]
    return modified_attrs


class ModelBase(object):
    """Base class for SQLAlchemy models with common fields and serialization.

    Provides standard fields (id, created_at, updated_at), serialization methods,
    and utilities for creating/updating model instances with support for settings
    fields and change tracking.

    Attributes:
        id: UUID primary key column.
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
        settings: Optional JSON field for storing model-specific settings.
        regular_settings_field: If True, treats settings as a regular field.
        combined_settings: If True, merges settings into the main dict during serialization.
        need_jsonable_encoder: If True, uses jsonable_encoder for data processing.
        valid_settings: List of valid setting keys allowed for this model.
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    settings = None
    regular_settings_field = False
    combined_settings = True
    need_jsonable_encoder = True
    valid_settings: List[str] = []

    @classmethod
    def get_fields(cls) -> list:
        """Return a list of column names excluding 'settings'.

        Returns:
            List of column names defined on the model's table, excluding 'settings'.
        """
        fields = list(cls.__table__.columns.keys())  # type: ignore
        if "settings" in fields:
            fields.remove("settings")
        return fields

    def get(
        self, excludes: set[str] | None = None, includes: set[str] | None = None
    ) -> dict[str, Any] | None:
        """Serialize the model instance to a dictionary with optional field
        filtering.

        Converts the model instance to a dictionary representation, optionally
        merging settings fields and applying inclusion/exclusion filters.

        Args:
            excludes: Set of field names to exclude from the result.
            includes: Set of field names to include in the result (if specified,
                only these fields will be included).

        Returns:
            Dictionary representation of the model, or None if instance is None.
        """
        if self is None:
            return

        excludes = excludes or set()
        includes = includes or set()

        model = dict(self.__dict__.items())

        if not self.regular_settings_field:
            if settings := model.get("settings"):
                if self.combined_settings:
                    model = {**settings, **model}
                else:
                    model["settings"] = [
                        {"key": key, "value": value} for key, value in settings.items()
                    ]

            if self.combined_settings and "settings" in model:
                model.pop("settings", None)

        model = {
            k: v
            for k, v in model.items()
            if not k.startswith("_")
            and k not in excludes
            and (not includes or k in includes)
        }
        return model

    @classmethod
    def create(cls, db: Session, data: dict[str, Any] | Any) -> "ModelBase":
        """Create a new model instance and persist it to the database.

        Processes the provided data, separating regular fields from settings,
        and creates a new database record.

        Args:
            db: SQLAlchemy session for database operations.
            data: Dictionary or model containing the data for the new instance.

        Returns:
            The newly created and persisted model instance.
        """
        data = jsonable_encoder(data) if cls.need_jsonable_encoder else data
        model_fields = {}

        if not cls.regular_settings_field:
            if cls.combined_settings:
                requested_settings = {}
            else:
                requested_settings = {
                    item["key"]: item["value"]
                    for item in (data.get("settings", []) or [])
                    if item["key"] in cls.valid_settings
                }
        else:
            requested_settings = {}

        for k, v in data.items():
            if k in cls.get_fields():
                model_fields[k] = v
            elif cls.valid_settings and k in cls.valid_settings:
                requested_settings[k] = v

        if cls.valid_settings and requested_settings:
            model_fields["settings"] = requested_settings

        new_model = cls(**model_fields)
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        return new_model

    def update(self, db: Session, data: dict[str, Any] | Any) -> "ModelBase":
        """Update the model instance with new data and persist changes.

        Processes the provided data, updates the instance attributes,
        tracks changes including settings modifications, and commits
        the changes to the database.

        Args:
            db: SQLAlchemy session for database operations.
            data: Dictionary or model containing the updated data.

        Returns:
            The updated model instance after refresh from database.
        """
        data = jsonable_encoder(data) if self.need_jsonable_encoder else data

        if not self.regular_settings_field:
            current_settings: Dict[str, Any] = self.settings or {}
            if self.combined_settings:
                requested_settings: Dict[str, Any] = {}
            else:
                requested_settings = {
                    item["key"]: item["value"]
                    for item in (data.get("settings", []) or [])
                    if item["key"] in self.valid_settings
                }
        else:
            current_settings = {}
            requested_settings = {}

        for k, v in data.items():
            if k in self.get_fields():
                setattr(self, k, v)
            elif (
                self.combined_settings
                and self.valid_settings
                and k in self.valid_settings
            ):
                requested_settings[k] = v

        if (
            not self.regular_settings_field
            and self.valid_settings
            and requested_settings
        ):
            self.settings = (
                {**current_settings, **requested_settings}
                if self.settings
                else requested_settings
            )

        changes = get_modified_keys(self)

        if not self.regular_settings_field:
            if current_settings or requested_settings:
                if "settings" in changes:
                    changes.remove("settings")

                changes.extend(
                    get_difference_between_dictionaries(
                        old_value={
                            k: v
                            for k, v in (current_settings or {}).items()
                            if k in requested_settings
                        },
                        new_value=requested_settings,
                    )
                )

        db.commit()
        db.refresh(self)
        return self
