"""Filter value extraction utilities for database searches.

Provides functions to query the database and extract available filter
options based on actual data, supporting select, number, and date filter
types.
"""

from typing import Any

from sqlalchemy import func, union
from sqlalchemy.orm import Session

__all__ = ("get_filters_value",)


def filters_mapper(
    db: Session,
    pre_conditions: list[Any],
    joins: list[dict[str, Any]],
    filter_item: dict[str, Any],
    conditions: list[Any],
) -> list[dict[str, Any]] | dict[str, Any] | None:
    """Extract unique values from database columns for filter options.

    Queries the database to find all unique values or ranges for a given filter,
    generating the available options that can be presented to users.

    Args:
        db: SQLAlchemy session for database queries.
        pre_conditions: List of base WHERE conditions to apply.
        joins: List of join configurations for related tables.
        filter_item: Dictionary defining the filter (type, columns, labels, etc.).
        conditions: Additional filter conditions to apply.

    Returns:
        For select filters: List of dicts with 'label' and 'value' keys.
        For number/date filters: Dict with 'min' and 'max' keys.
        None if filter type is not supported.
    """
    columns = filter_item.get("columns")
    columns_type = filter_item.get("type", "select")

    if columns_type in {"select", "select_array"}:
        if not columns:
            return []
        distinct_names_query = []
        for column in columns:
            query = db.query(
                func.jsonb_array_elements_text(column)
                if filter_item.get("is_json", False)
                else column
            )

            for join_item in joins:
                query = query.join(**join_item)

            distinct_names_query.append(
                query.filter(*pre_conditions, *conditions).distinct()
            )

        values = []
        db_values = list(
            map(lambda x: x[0], db.execute(union(*distinct_names_query)).fetchall())
        )
        if columns_type == "select_array":
            for db_value in db_values:
                if isinstance(db_value, list):
                    values.extend(db_value)
        else:
            if isinstance(db_values, list):
                values.extend(db_values)

        enum = filter_item.get("enum")
        labels = filter_item.get("labels", {})
        items = [
            {
                "label": labels.get(enum(value) if enum else value, value),
                "value": enum(value).name if enum else value,
            }
            for value in values
            if value is not None
        ]
        items = sorted(items, key=lambda x: x.get("label") or "")
    elif columns_type in ["number", "date"]:
        if not columns:
            return None
        main_query = db.query(
            func.least(*list(map(func.min, columns))),
            func.greatest(*list(map(func.max, columns))),
        )
        for join_item in joins:
            main_query = main_query.join(**join_item)

        result = main_query.filter(*pre_conditions, *conditions).first()
        if result is None:
            range_items = {"min": None, "max": None}
        else:
            min_value, max_value = result
            range_items = {"min": min_value, "max": max_value}
        return range_items
    else:
        return None

    return items


def get_filters_value(
    db: Session,
    pre_conditions: list[Any],
    joins: list[dict[str, Any]],
    filters: list[dict[str, Any]],
    names_conditions: dict[str, list[Any]],
) -> list[dict[str, Any]]:
    """Build a list of available filter options from database data.

    Queries the database for each defined filter to generate the available
    options based on actual data, applying pre-conditions and cross-filter
    conditions.

    Args:
        db: SQLAlchemy session for database queries.
        pre_conditions: List of base WHERE conditions to always apply.
        joins: List of join configurations for related tables.
        filters: List of filter definitions.
        names_conditions: Dictionary mapping filter names to their conditions.

    Returns:
        List of available filter dictionaries, each containing:
            - label: Display label for the filter
            - name: Internal filter name
            - type: Filter type (select, number, date, etc.)
            - value: Available options or range for the filter
    """
    available_filters = []
    for filter_item in filters:
        filter_name_conditions = names_conditions.get(filter_item["name"])
        if filter_name_conditions is None:
            continue
        filter_mapping_result = filters_mapper(
            db=db,
            pre_conditions=pre_conditions,
            joins=joins,
            filter_item=filter_item,
            conditions=filter_name_conditions,
        )
        filter_label = filter_item.get("label")
        filter_type = filter_item.get("type")
        filter_name = filter_item.get("name")
        if filter_mapping_result is not None:
            if filter_type in {"select", "select_array"}:
                available_filters.append(
                    {
                        "label": filter_label,
                        "name": filter_name,
                        "type": filter_type,
                        "value": filter_mapping_result,
                    }
                )
            elif filter_type in ["number", "date"]:
                available_filters.append(
                    {
                        "label": filter_label,
                        "name": filter_name,
                        "type": filter_type,
                        "value": filter_mapping_result,
                    }
                )
            else:
                available_filters.append(
                    {
                        "label": filter_label,
                        "name": filter_name,
                        "type": filter_type,
                    }
                )

    return available_filters
