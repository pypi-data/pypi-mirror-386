"""Advanced database search and filtering utilities.

Provides the get_list function for executing complex search queries with
filtering, pagination, sorting, and metadata generation capabilities.
"""

from enum import Enum
from math import ceil
from typing import Any, Dict, List, Literal, Type, overload

from sqlalchemy import distinct as distinct_func
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .schema import (
    AvailableFilters, SearchResult, Payload,
    SelectedFilters, RowsListDict, RowsListModelType,
    ModelType
)
from .search_utils.filter_values import get_filters_value
from .search_utils.free_search import free_search
from .search_utils.make_condition import make_condition
from .search_utils.selected_filters import make_selected_filters

__all__ = ("get_list",)


# Overload 1: export_mode=True, return_as_dict=True -> list[dict]
@overload
def get_list(
    current_query: dict[str, Any],
    db: Session,
    model: Type[ModelType],
    joins: list[dict[str, Any]] | None = None,
    pre_conditions: list[Any] | None = None,
    filters: list[dict[str, Any]] | None = None,
    searchable_columns: list[Any] | None = None,
    exact_search: bool = False,
    search_tokenizer: bool = False,
    search_similarity_threshold: float = 0.1,
    options: list[Any] | None = None,
    primary_column: str = "id",
    sorting_null_at_the_end: bool = True,
    return_available_filters: bool = True,
    return_selected_filters: bool = True,
    return_rows_data: bool = True,
    export_mode: Literal[True] = True,
    return_as_dict: Literal[True] = True,
    return_as_dict_parameters: dict[str, Any] | None = None,
    unique: bool = True,
) -> RowsListDict: ...


# Overload 2: export_mode=True, return_as_dict=False -> list[ModelType]
@overload
def get_list(
    current_query: dict[str, Any],
    db: Session,
    model: Type[ModelType],
    joins: list[dict[str, Any]] | None = None,
    pre_conditions: list[Any] | None = None,
    filters: list[dict[str, Any]] | None = None,
    searchable_columns: list[Any] | None = None,
    exact_search: bool = False,
    search_tokenizer: bool = False,
    search_similarity_threshold: float = 0.1,
    options: list[Any] | None = None,
    primary_column: str = "id",
    sorting_null_at_the_end: bool = True,
    return_available_filters: bool = True,
    return_selected_filters: bool = True,
    return_rows_data: bool = True,
    export_mode: Literal[True] = True,
    return_as_dict: Literal[False] = False,
    return_as_dict_parameters: dict[str, Any] | None = None,
    unique: bool = True,
) -> RowsListModelType: ...


# Overload 3: export_mode=False -> GetListResult
@overload
def get_list(
    current_query: dict[str, Any],
    db: Session,
    model: Type[ModelType],
    joins: list[dict[str, Any]] | None = None,
    pre_conditions: list[Any] | None = None,
    filters: list[dict[str, Any]] | None = None,
    searchable_columns: list[Any] | None = None,
    exact_search: bool = False,
    search_tokenizer: bool = False,
    search_similarity_threshold: float = 0.1,
    options: list[Any] | None = None,
    primary_column: str = "id",
    sorting_null_at_the_end: bool = True,
    return_available_filters: bool = True,
    return_selected_filters: bool = True,
    return_rows_data: bool = True,
    export_mode: Literal[False] = False,
    return_as_dict: bool = True,
    return_as_dict_parameters: dict[str, Any] | None = None,
    unique: bool = True,
) -> SearchResult: ...


# Implementation
def get_list(
    current_query: dict[str, Any],
    db: Session,
    model: Type[ModelType],
    joins: list[dict[str, Any]] | None = None,
    pre_conditions: list[Any] | None = None,
    filters: list[dict[str, Any]] | None = None,
    searchable_columns: list[Any] | None = None,
    exact_search: bool = False,
    search_tokenizer: bool = False,
    search_similarity_threshold: float = 0.1,
    options: list[Any] | None = None,
    primary_column: str = "id",
    sorting_null_at_the_end: bool = True,
    return_available_filters: bool = True,
    return_selected_filters: bool = True,
    return_rows_data: bool = True,
    export_mode: bool = False,
    return_as_dict: bool = True,
    return_as_dict_parameters: dict[str, Any] | None = None,
    unique: bool = True,
) -> SearchResult | RowsListModelType | RowsListDict:
    """Execute a complex database search with filtering, pagination, sorting, and metadata.

    This function provides a comprehensive search interface for SQLAlchemy models,
    combining multiple query capabilities into a single operation:
    - Dynamic filtering (select, number, date ranges)
    - Free-text search with fuzzy matching
    - Multi-column sorting with null handling
    - Pagination with metadata
    - Join support for related tables
    - Result deduplication
    - Flexible output formats (models, dicts, or full metadata)

    The function builds a query in stages:
    1. Applies joins and pre-conditions
    2. Processes dynamic filters from current_query
    3. Applies free-text search across searchable_columns
    4. Deduplicates by primary_column if unique=True
    5. Applies sorting and pagination
    6. Generates filter metadata (available and selected options)

    Args:
        current_query: Query parameters dictionary containing:
            - search (str, optional): Free-text search query
            - page (int, optional): Current page number (default: 1)
            - items_per_page (int, optional): Items per page (default: 30)
            - sorting (list, optional): List of {"sort_by": column, "order_by": "asc"|"desc"}
            - <filter_name>: Values for each filter defined in `filters` parameter
        db: Active SQLAlchemy database session for executing queries.
        model: SQLAlchemy model class to query (must inherit from DeclarativeBase).
        joins: Optional list of join configurations. Each dict should contain
            SQLAlchemy join parameters (e.g., {"target": RelatedModel, "onclause": condition}).
        pre_conditions: Optional list of SQLAlchemy filter expressions to always
            apply (e.g., [Model.deleted_at.is_(None), Model.active == True]).
        filters: Optional list of filter definitions. Each dict should contain:
            - name (str): Parameter name in current_query
            - label (str): Display label for the filter
            - type (str): Filter type ("select", "select_array", "number", "date")
            - columns (list): SQLAlchemy columns to filter on
            - Additional type-specific configuration
        searchable_columns: Optional list of SQLAlchemy column objects to search
            across when current_query contains a "search" parameter.
        exact_search: If True, search matches exact phrases. If False, uses
            fuzzy matching with similarity threshold (default: False).
        search_tokenizer: If True, enables full-text search tokenization for
            better word-based matching (default: False).
        search_similarity_threshold: Minimum similarity score (0.0-1.0) for fuzzy
            search matching. Lower values are more permissive (default: 0.1).
        options: Optional list of SQLAlchemy query options for eager loading
            (e.g., [joinedload(Model.relation), selectinload(Model.items)]).
        primary_column: Name of the primary key column used for deduplication
            when unique=True (default: "id").
        sorting_null_at_the_end: If True, null values appear last in sorted results
            regardless of sort direction (default: True).
        return_available_filters: If True, includes available filter options in
            the result, showing all possible values for each filter (default: True).
        return_selected_filters: If True, includes currently active filters in
            the result for UI state management (default: True).
        return_rows_data: If True, includes the actual data rows in the result.
            Set to False to get only metadata and counts (default: True).
        export_mode: If True, returns only the rows list without any metadata
            wrapper. Useful for data exports (default: False).
        return_as_dict: If True, converts model instances to dictionaries using
            the model's to_dict() method (default: True).
        return_as_dict_parameters: Optional dict of parameters to pass to the
            model's to_dict() method for controlling serialization behavior.
        unique: If True, deduplicates results by primary_column. Essential when
            using joins that may create duplicate rows (default: True).

    Returns:
        SearchResult: When export_mode=False, returns a SearchResult object containing:
            - payload: Payload object with query parameters and pagination metadata
              (page, items_per_page, total_row, last_page, has_next, sorting, search)
            - available_filters: List of AvailableFilter objects (if return_available_filters=True)
            - selected_filters: List of SelectedFilter objects (if return_selected_filters=True)
            - rows_data: RowsListDict or RowsListModelType (if return_rows_data=True)
        
        RowsListDict: When export_mode=True and return_as_dict=True, returns list of
            dictionaries, each representing a row.
        
        RowsListModelType: When export_mode=True and return_as_dict=False, returns
            list of model instances.

    Raises:
        AttributeError: If primary_column doesn't exist on the model.
        SQLAlchemyError: If database query execution fails.

    Example:
        >>> from sqlalchemy.orm import Session
        >>> from myapp.models import User
        >>> from dtpyfw.db import get_list
        >>> 
        >>> query = {
        ...     "search": "john",
        ...     "page": 1,
        ...     "items_per_page": 20,
        ...     "status": "active",
        ...     "age_min": 18,
        ...     "age_max": 65,
        ...     "sorting": [{"sort_by": "created_at", "order_by": "desc"}]
        ... }
        >>> 
        >>> filters = [
        ...     {
        ...         "name": "status",
        ...         "label": "Status",
        ...         "type": "select",
        ...         "columns": [User.status]
        ...     },
        ...     {
        ...         "name": "age",
        ...         "label": "Age",
        ...         "type": "number",
        ...         "columns": [User.age]
        ...     }
        ... ]
        >>> 
        >>> result = get_list(
        ...     current_query=query,
        ...     db=session,
        ...     model=User,
        ...     filters=filters,
        ...     searchable_columns=[User.name, User.email],
        ...     pre_conditions=[User.deleted_at.is_(None)]
        ... )
        >>> 
        >>> print(f"Total users: {result.payload.total_row}")
        >>> print(f"Page {result.payload.page} of {result.payload.last_page}")
        >>> for user_dict in result.rows_data:
        ...     print(user_dict["name"])
    """
    joins = joins or []
    filters = filters or []
    searchable_columns = searchable_columns or []
    pre_conditions = pre_conditions or []
    options = options or []
    return_as_dict_parameters = return_as_dict_parameters or {}

    page = current_query.get("page") or 1
    items_per_page = current_query.get("items_per_page") or 30

    orm_primary_column = getattr(model, primary_column)

    # Create Initial Model Query
    main_query = select(model)

    if unique:
        count_query = select(func.count(distinct_func(orm_primary_column))).select_from(
            model
        )
    else:
        count_query = select(func.count()).select_from(model)

    for join_item in joins:
        main_query = main_query.join(**join_item)
        count_query = count_query.join(**join_item)

    main_query = main_query.where(*pre_conditions)
    count_query = count_query.where(*pre_conditions)

    # Initialize rows and conditions
    conditions = []
    names_conditions: Dict[str, List[Any]] = {
        filter_item["name"]: [] 
        for filter_item in filters 
        if filter_item.get("name") is not None
    }

    for filter_item in filters:
        name = filter_item.get("name")
        columns = filter_item.get("columns")
        if not columns or not name:
            continue
        
        values = current_query.get(name)
        if not values:
            continue

        target_condition = make_condition(filter_item=filter_item, values=values)
        if target_condition is not None:
            conditions.append(target_condition)
            for inner_name, inner_name_values in names_conditions.items():
                if inner_name != name:
                    inner_name_values.append(target_condition)

    if conditions:
        main_query = main_query.where(*conditions)
        count_query = count_query.where(*conditions)

    if search_query := current_query.get("search"):
        search_conditions, search_sort = free_search(
            columns=searchable_columns,
            query=search_query,
            threshold=search_similarity_threshold,
            exact=exact_search,
            tokenize=search_tokenizer,
        )
        main_query = main_query.where(*search_conditions)
        count_query = count_query.where(*search_conditions)
    else:
        search_sort = None

    if unique:
        main_query = main_query.distinct(orm_primary_column)
        main_query.order_by(orm_primary_column)

    dedup_cte = main_query.cte("dedup_cte")

    sorting = current_query.get("sorting") or []

    order_by_list: List[Any] = []
    if search_sort is not None:
        order_by_list.extend(search_sort)
    elif sorting := (current_query.get("sorting") or []):
        for item in sorting:
            order_by = item.get("order_by")
            sort_by = item.get("sort_by")

            if sort_by is None or order_by is None:
                continue

            sort_by = sort_by.value if isinstance(sort_by, Enum) else sort_by
            order_by = order_by.value if isinstance(order_by, Enum) else order_by

            sort_by_model = (
                getattr(model, sort_by) if isinstance(sort_by, str) else sort_by
            )
            order_by_model = (
                getattr(sort_by_model, order_by)
                if isinstance(order_by, str)
                else order_by
            )

            if sorting_null_at_the_end:
                order_by_list.append(order_by_model().nulls_last())
            else:
                order_by_list.append(order_by_model())

    final_query = select(model).join(dedup_cte, orm_primary_column == dedup_cte.c.id)

    if options:
        final_query = final_query.options(*options)

    if order_by_list:
        final_query = final_query.order_by(*order_by_list)

    if items_per_page and page:
        final_query = final_query.limit(items_per_page).offset(
            (page - 1) * items_per_page
        )

    count_query = count_query.order_by(None)

    rows: RowsListModelType | RowsListDict | None
    if return_rows_data:
        db_rows = db.execute(final_query).unique().scalars().all()
        if return_as_dict:
            rows = RowsListDict.model_validate([row.to_dict(**return_as_dict_parameters) for row in db_rows])
        else:
            rows = RowsListModelType.model_validate(list(db_rows))
    else:
        rows = None

    if export_mode and return_rows_data and rows is not None:
        return rows
    else:
        count = db.execute(count_query).scalar_one()
        current_query["total_row"] = count

        # Calculate pagination-related information
        if items_per_page and page:
            last_page = ceil(count / items_per_page)
            current_query["last_page"] = last_page
            current_query["has_next"] = last_page > page
            current_query["page"] = page
            current_query["items_per_page"] = items_per_page

        # Ensure sorting exists before validation
        if "sorting" not in current_query:
            current_query["sorting"] = []

        payload = Payload.model_validate(current_query)

        if return_rows_data and rows is not None:
            rows_data = rows
        else:
            rows_data = None

        available_filters: AvailableFilters | None = None
        if return_available_filters:
            available_filters: AvailableFilters = (
                get_filters_value(
                    db=db,
                    pre_conditions=pre_conditions,
                    joins=joins,
                    filters=filters,
                    names_conditions=names_conditions,
                )
                if filters is not None
                else []
            )

        selected_filters: SelectedFilters | None = None
        if return_selected_filters:
            selected_filters: SelectedFilters = make_selected_filters(
                current_query=current_query,
                filters=filters,
            )

        return SearchResult(
            payload=payload,
            rows_data=rows_data,
            available_filters=available_filters,
            selected_filters=selected_filters,
        )
