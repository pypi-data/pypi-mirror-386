"""Pydantic schemas for database search and filtering functionality.

Defines data models for search queries, filters, pagination, and results
used in the database search utilities. Supports select, number, date,
and free-text search filter types.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, List, Literal, Optional, Union, TypeVar, Dict

from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel, ConfigDict, Field, RootModel


ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class RowsListModelType(RootModel[List[Any]]):
    """Root model representing a list of SQLAlchemy model instances from search
    results.
    
    Note: Uses List[Any] instead of List[ModelType] to avoid Pydantic schema
    generation errors with SQLAlchemy's DeclarativeBase at class definition time.
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class RowsListDict(RootModel[List[Dict[str, Any]]]):
    """Root model representing a list of row dictionaries from search
    results."""


class AvailableFilterType(Enum):
    """Enumeration of available filter types for database searches."""

    select = "select"
    select_array = "select_array"
    number = "number"
    date = "date"
    search = "search"


class AvailableFilterSelectItem(BaseModel):
    """Represents a single option in a select-type filter.

    Attributes:
        label: Display label for the option.
        value: The actual value to use in filtering.
    """

    label: str
    value: Any


class AvailableFilterNumberItem(BaseModel):
    """Range boundaries for a numeric filter.

    Attributes:
        min: Minimum value in the range.
        max: Maximum value in the range.
    """

    min: Optional[int]
    max: Optional[int]


class AvailableFilterDateItem(BaseModel):
    """Date range boundaries for a date filter.

    Attributes:
        min: Earliest date in the range.
        max: Latest date in the range.
    """

    min: Optional[datetime]
    max: Optional[datetime]


AvailableFilterValue = list[AvailableFilterSelectItem] | AvailableFilterNumberItem | AvailableFilterDateItem | None


class AvailableFilterSelect(BaseModel):
    """Select-type filter with discrete options.

    Attributes:
        label: Display label for the filter.
        name: Internal name/key for the filter.
        type: Filter type identifier (select).
        value: List of available options for this filter.
    """

    label: str
    name: str
    type: Literal[AvailableFilterType.select, AvailableFilterType.select_array]
    value: list[AvailableFilterSelectItem]


class AvailableFilterNumber(BaseModel):
    """Numeric range filter.

    Attributes:
        label: Display label for the filter.
        name: Internal name/key for the filter.
        type: Filter type identifier (number).
        value: Min/max range for numeric filtering.
    """

    label: str
    name: str
    type: Literal[AvailableFilterType.number]
    value: AvailableFilterNumberItem


class AvailableFilterDate(BaseModel):
    """Date range filter.

    Attributes:
        label: Display label for the filter.
        name: Internal name/key for the filter.
        type: Filter type identifier (date).
        value: Min/max date range for filtering.
    """

    label: str
    name: str
    type: Literal[AvailableFilterType.date]
    value: AvailableFilterDateItem


AvailableFilter = Annotated[
    Union[
        AvailableFilterSelect,
        AvailableFilterNumber,
        AvailableFilterDate,
    ],
    Field(discriminator="type"),
]

AvailableFilters = List[AvailableFilter]


class SearchType(Enum):
    """Enumeration of search and filter types for selected filters."""

    select = "select"
    select_array = "select_array"
    number = "number"
    date = "date"
    search = "search"


class SelectedFilterSelect(BaseModel):
    """Selected value for a select-type filter.

    Attributes:
        label: Display label for the selected filter.
        name: Internal name/key for the filter.
        type: Filter type identifier (select).
        value: The selected value (string or enum).
    """

    label: str
    name: str
    type: Literal[SearchType.select, SearchType.select_array]
    value: str | Enum


class SelectedFilterNumberItem(BaseModel):
    """Selected numeric range values.

    Attributes:
        min: Selected minimum value.
        max: Selected maximum value.
    """

    min: int
    max: int


class SelectedFilterNumber(BaseModel):
    """Selected numeric range filter.

    Attributes:
        label: Display label for the selected filter.
        name: Internal name/key for the filter.
        type: Filter type identifier (number).
        value: Selected min/max range.
    """

    label: str
    name: str
    type: Literal[SearchType.number]
    value: SelectedFilterNumberItem


class SelectedFilterDateItem(BaseModel):
    """Selected date range values.

    Attributes:
        min: Selected start date.
        max: Selected end date.
    """

    min: datetime
    max: datetime


class SelectedFilterDate(BaseModel):
    """Selected date range filter.

    Attributes:
        label: Display label for the selected filter.
        name: Internal name/key for the filter.
        type: Filter type identifier (date).
        value: Selected date range.
    """

    label: str
    name: str
    type: Literal[SearchType.date]
    value: SelectedFilterDateItem


class SelectedFilterSearch(BaseModel):
    """Selected free-text search filter.

    Attributes:
        label: Display label for the search.
        name: Internal name/key for the filter.
        type: Filter type identifier (search).
        value: The search query string.
    """

    label: str
    name: str
    type: Literal[SearchType.search]
    value: str


SelectedFilter = Annotated[
    Union[
        SelectedFilterSelect,
        SelectedFilterNumber,
        SelectedFilterDate,
        SelectedFilterSearch,
    ],
    Field(discriminator="type"),
]

SelectedFilters = List[SelectedFilter]


class PayloadSorting(BaseModel):
    """Sorting configuration for search results.

    Attributes:
        order_by: Sort direction ('asc' or 'desc', may be enum).
        sort_by: Field name to sort by (may be enum).
    """

    order_by: str | Enum
    sort_by: str | Enum


class Payload(BaseModel):
    """Search query payload and pagination metadata.

    Attributes:
        search: Free-text search query string.
        sorting: List of sorting configurations.
        page: Current page number.
        items_per_page: Number of items per page.
        total_row: Total number of matching rows.
        last_page: Last available page number.
        has_next: Whether there are more pages available.
    """

    search: Optional[str] = None
    sorting: list[PayloadSorting]
    page: int = 1
    items_per_page: int = 30
    total_row: int
    last_page: int
    has_next: bool

    model_config = ConfigDict(extra="allow")


class SearchResult(BaseModel):
    """Complete search result including data and filter information.

    Attributes:
        payload: Search query parameters and pagination metadata.
        available_filters: All available filters with their options.
        selected_filters: Currently applied filters.
        rows_data: The actual data rows matching the search criteria.
    """

    payload: Payload | None = None
    available_filters: List[AvailableFilter] | None = None
    selected_filters: List[SelectedFilter] | None = None
    rows_data: RowsListModelType | RowsListDict | None = None
