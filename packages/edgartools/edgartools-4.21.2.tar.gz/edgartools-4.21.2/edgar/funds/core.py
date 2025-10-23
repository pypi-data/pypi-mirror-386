"""
Core classes for working with investment funds.

This module provides the main classes used to interact with investment funds:
- Fund: Represents an investment fund entity
- FundClass: Represents a specific share class of a fund
- FundSeries: Represents a fund series
"""
import logging
from typing import TYPE_CHECKING, List, Optional, Union, Dict, Any

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from edgar.entity.core import Entity
from edgar.richtools import repr_rich

if TYPE_CHECKING:
    from edgar._filings import Filings
    from edgar.entity.data import EntityData

log = logging.getLogger(__name__)

__all__ = ['Fund', 'FundCompany', 'FundClass', 'FundSeries', 'get_fund_company', 'get_fund_class', 'get_fund_series', 'find_fund']


class FundCompany(Entity):
    """
    Represents an investment fund that files with the SEC.

    Provides fund-specific functionality like share classes, series information,
    portfolio holdings, etc.
    """

    def __init__(self,
                 cik_or_identifier: Union[str, int],
                 fund_name:str=None,
                 all_series:Optional[List['FundSeries']] = None):
        # Import locally to avoid circular imports
        from edgar.funds.data import resolve_fund_identifier

        # Handle fund-specific identifiers
        super().__init__(resolve_fund_identifier(cik_or_identifier))
        self._name = fund_name
        self.all_series:Optional[List['FundSeries']] = all_series or []
        self._cached_portfolio = None


    @property
    def name(self):
        """Get the name of the company."""
        return self._name or super().name

    def list_series(self) -> List['FundSeries']:
        """
        List all fund series associated with this company.

        Returns:
            List of FundSeries instances
        """
        return self.all_series

    @property
    def data(self) -> 'EntityData':
        """Get detailed data for this fund."""
        base_data = super().data

        # If we already have fund-specific data, return it
        if hasattr(base_data, 'is_fund') and base_data.is_fund:
            return base_data

        # Otherwise, try to convert to fund-specific data
        # This could be enhanced in the future
        return base_data

    def __str__(self):
        return f"{self.name} [{self.cik}]"


    def __rich__(self):
        """Creates a rich representation of the fund with detailed information."""
        return super().__rich__()

    def __repr__(self):
        return repr_rich(self.__rich__())

class FundClass:
    """
    Represents a specific class of an investment fund.

    Fund classes typically have their own ticker symbols and fee structures,
    but belong to the same underlying fund. Each class belongs to a specific
    fund series.
    """

    def __init__(self, class_id: str, name: Optional[str] = None,
                ticker: Optional[str] = None, series: Optional['FundSeries'] = None):
        self.class_id = class_id
        self.name = name
        self.ticker = ticker
        self.series = series  # The series ID this class belongs to

    def __str__(self):
        ticker_str = f" - {self.ticker}" if self.ticker else ""
        return f"FundClass({self.name} [{self.class_id}]{ticker_str})"

    def get_classes(self) -> List['FundClass']:
        """Get all share classes in the same series as this class."""
        if self.series and self.series.series_id:
            from edgar.funds.data import get_fund_object
            full_series = get_fund_object(self.series.series_id)
            if full_series and hasattr(full_series, 'get_classes'):
                return full_series.get_classes()
        return [self]  # fallback

    def __repr__(self):
        return self.__str__()

    def __rich__(self):
        """Creates a rich representation of the fund class."""
        table = Table(
            title=None,
            box=box.ROUNDED,
            show_header=True
        )

        table.add_column("Fund", style="bold")
        table.add_column("Class ID", style="bold")
        table.add_column("Series ID", style="bold cyan")
        table.add_column("Ticker", style="bold yellow")

        table.add_row(
                self.name,
                self.class_id, 
                self.series.series_id or "Unknown",
                self.ticker or ""
        )

        return Panel(
                table,
                title=f"🏦 {self.name}",
                subtitle="Fund Class"
        )

class FundSeries:
    """Represents a fund series with multiple share classes."""

    def __init__(self, series_id: str, name: str,
                 fund_classes:Optional[List[FundClass]]=None,
                 fund_company: Optional[FundCompany] = None):
        self.series_id = series_id
        self.name = name
        self.fund_classes:List[FundClass] = fund_classes or []
        self.fund_company: Optional[FundCompany] = fund_company

    def get_classes(self) -> List[FundClass]:
        """
        Get all share classes in this series.

        Returns:
            List of FundClass instances belonging to this specific series
        """
        return self.fund_classes

    def get_filings(self, **kwargs) -> 'Filings':
        """
        Get filings for this fund series.

        Args:
            **kwargs: Filtering parameters passed to get_filings

        Returns:
            Filings object with filtered filings
        """
        return self.fund_company.get_filings(**kwargs)

    def __str__(self):
        return f"FundSeries({self.name} [{self.series_id}])"

    def __repr__(self):
        return repr_rich(self.__rich__())

    def __rich__(self):
        """Creates a rich representation of the fund series."""

        # Classes information
        classes = self.get_classes()
        classes_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
        classes_table.add_column("Class ID")
        classes_table.add_column("Class Name")
        classes_table.add_column("Ticker", style="bold yellow")

        for class_obj in classes:
            classes_table.add_row(
                        class_obj.class_id,
                    class_obj.name,
                    class_obj.ticker or "-"
             )

        classes_panel = Panel(
                classes_table,
                title="📊 Share Classes",
                border_style="grey50"
        )

        content = Group(classes_panel)
        return Panel(
            content,
            title=f"🏦 {self.name} [{self.series_id}]",
            subtitle="Fund Series"
        )

def find_fund(identifier: str) -> Union[FundCompany, FundSeries, FundClass]:
    """
    Smart factory that finds and returns the most appropriate fund entity.

    This function takes any type of fund identifier and returns the most specific
    entity that matches it. For a series ID, it returns a FundSeries. For a class ID
    or ticker, it returns a FundClass. For a company CIK, it returns a FundCompany.

    Args:
        identifier: Fund ticker (e.g., 'VFINX'), Series ID (e.g., 'S000001234'),
                  Class ID (e.g., 'C000012345'), or CIK number

    Returns:
        The most specific fund entity that matches the identifier:
        - FundClass for tickers and class IDs
        - FundSeries for series IDs
        - FundCompany for company CIKs
    """
    # Check for Series ID (S000XXXXX)
    if isinstance(identifier, str) and identifier.upper().startswith('S') and identifier[1:].isdigit():
        return get_fund_series(identifier)

    # Check for Class ID (C000XXXXX)
    if isinstance(identifier, str) and identifier.upper().startswith('C') and identifier[1:].isdigit():
        return get_fund_class(identifier)

    # Check for ticker symbol
    if is_fund_class_ticker(identifier):
        return get_fund_class(identifier)

    # Default to returning a FundCompany
    return get_fund_company(identifier)


# === Specialized Getter Functions ===

def get_fund_company(cik_or_identifier: Union[str, int]) -> FundCompany:
    """
    Get a fund company by its CIK or identifier.

    Args:
        cik_or_identifier: CIK number or other identifier

    Returns:
        FundCompany instance
    """
    return FundCompany(cik_or_identifier)


def get_fund_series(series_id: str) -> FundSeries:
    """
    Get a fund series by its Series ID.

    Args:
        series_id: Series ID (e.g., 'S000001234')

    Returns:
        FundSeries instance

    Raises:
        ValueError: If the series cannot be found
    """
    from edgar.funds.data import get_fund_object

    fund_series: Optional[FundSeries] = get_fund_object(series_id)
    return fund_series


def get_fund_class(class_id_or_ticker: str) -> FundClass:
    """
    Get a fund class by its Class ID or ticker.

    Args:
        class_id_or_ticker: Class ID (e.g., 'C000012345') or ticker symbol (e.g., 'VFINX')

    Returns:
        FundClass instance

    Raises:
        ValueError: If the class cannot be found
    """
    from edgar.funds.data import get_fund_object
    fund_class: FundClass = get_fund_object(class_id_or_ticker)
    return fund_class


# === Helper Functions ===

def is_fund_class_ticker(identifier: str) -> bool:
    """
    Determine if the given identifier is a fund class ticker.

    Args:
        identifier: The identifier to check

    Returns:
        True if it's a fund class ticker, False otherwise
    """
    from edgar.funds.data import is_fund_ticker
    return is_fund_ticker(identifier)


class Fund:
    """
    Unified wrapper for fund entities that provides a consistent interface
    regardless of the identifier type (ticker, series ID, class ID, or CIK).

    This class serves as a user-friendly entry point to the fund domain model.
    It internally resolves the appropriate entity type and provides access to
    the full hierarchy.

    Examples:
        ```python
        # Create a Fund object from any identifier
        fund = Fund("VFINX")         # From ticker
        fund = Fund("S000002277")    # From series ID
        fund = Fund("0000102909")    # From CIK

        # Access the hierarchy
        print(fund.name)              # Name of the entity
        print(fund.company.name)      # Name of the fund company
        print(fund.series.name)       # Name of the fund series
        print(fund.share_class.ticker) # Ticker of the share class
        ```
    """

    def __init__(self, identifier: Union[str, int]):
        """
        Initialize a Fund object from any identifier.

        Args:
            identifier: Any fund identifier (ticker, series ID, class ID, or CIK)
        """
        self._original_identifier = str(identifier)
        self._target_series_id = None  # New: specific series if determinable

        # Handle ticker resolution to series
        if isinstance(identifier, str) and self._is_fund_ticker(identifier):
            from edgar.funds.series_resolution import TickerSeriesResolver
            target_series_id = TickerSeriesResolver.get_primary_series(identifier)
            if target_series_id:
                self._target_series_id = target_series_id

        # Use existing find_fund to get the appropriate entity
        self._entity = find_fund(identifier)

        # Set up references to the full hierarchy
        if isinstance(self._entity, FundClass):
            self._class = self._entity
            self._series = self._class.series
            self._company = self._series.fund_company if self._series else None
        elif isinstance(self._entity, FundSeries):
            self._class = None
            self._series = self._entity
            self._company = self._series.fund_company
        elif isinstance(self._entity, FundCompany):
            self._class = None
            self._series = None
            self._company = self._entity

    def _is_fund_ticker(self, identifier: str) -> bool:
        """Check if an identifier appears to be a fund ticker"""
        from edgar.funds.series_resolution import TickerSeriesResolver
        series_list = TickerSeriesResolver.resolve_ticker_to_series(identifier)
        return len(series_list) > 0

    @property
    def company(self) -> Optional[FundCompany]:
        """Get the fund company (may be None if not resolved)"""
        return self._company

    @property
    def series(self) -> Optional[FundSeries]:
        """Get the fund series (may be None if only company was identified)"""
        return self._series

    @property
    def share_class(self) -> Optional[FundClass]:
        """Get the share class (may be None if only series or company was identified)"""
        return self._class

    @property
    def name(self) -> str:
        """Get the name of the fund entity"""
        return self._entity.name

    @property
    def identifier(self) -> str:
        """Get the primary identifier of the fund entity"""
        if isinstance(self._entity, FundClass):
            return self._entity.class_id
        elif isinstance(self._entity, FundSeries):
            return self._entity.series_id
        elif isinstance(self._entity, FundCompany):
            return str(self._entity.cik)
        return ""

    @property
    def ticker(self) -> Optional[str]:
        """Get the ticker symbol (only available for share classes)"""
        if self._class:
            return self._class.ticker
        return None

    def get_filings(self, series_only: bool = False, **kwargs) -> 'Filings':
        """
        Get filings for this fund entity.

        This delegates to the appropriate entity's get_filings method.

        Args:
            series_only: If True and we have target series context, filter to only relevant series
            **kwargs: Filtering parameters passed to get_filings

        Returns:
            Filings object with filtered filings
        """
        # Get base filings
        filings = None
        if hasattr(self._entity, 'get_filings'):
            filings = self._entity.get_filings(series_only=series_only, **kwargs)
        elif self._series and hasattr(self._series, 'get_filings'):
            filings = self._series.get_filings(series_only=series_only, **kwargs)
        elif self._company and hasattr(self._company, 'get_filings'):
            filings = self._company.get_filings(series_only=series_only, **kwargs)

        if not filings:
            from edgar._filings import Filings
            return Filings([])

        # Apply series filtering if requested and we have target series context
        if series_only and self._target_series_id and kwargs.get('form') in ['NPORT-P', 'NPORT-EX', 'N-PORT', 'N-PORT/A']:
            # For now, return the original filings as we'd need to parse each filing
            # to determine series match. This could be enhanced in the future.
            pass

        return filings

    def get_series(self) -> Optional[FundSeries]:
        """
        Get the specific series for the original ticker if determinable.

        Returns:
            FundSeries if we can determine a specific series, None otherwise
        """
        if self._target_series_id:
            # Handle ETF synthetic series IDs
            if self._target_series_id.startswith("ETF_"):
                # Extract CIK from ETF series ID
                cik = self._target_series_id.replace("ETF_", "")
                try:
                    # Create ETF-specific series
                    from edgar.funds.series_resolution import TickerSeriesResolver
                    series_list = TickerSeriesResolver.resolve_ticker_to_series(self._original_identifier)
                    if series_list and len(series_list) > 0:
                        series_info = series_list[0]  # Get the ETF series info

                        # Create FundSeries for ETF
                        etf_company = FundCompany(cik_or_identifier=int(cik), fund_name=series_info.series_name)
                        return FundSeries(
                            series_id=self._target_series_id,
                            name=series_info.series_name or f"ETF Series for {self._original_identifier}",
                            fund_company=etf_company
                        )
                except Exception as e:
                    log.debug(f"Failed to create ETF series for {self._target_series_id}: {e}")
            else:
                # Regular mutual fund series - try to get by ID
                try:
                    return get_fund_series(self._target_series_id)
                except Exception as e:
                    log.debug(f"Failed to get fund series {self._target_series_id}: {e}")

        # Fallback to current series if available
        return self._series

    def get_resolution_diagnostics(self) -> Dict[str, Any]:
        """Get detailed information about how this Fund was resolved."""
        if self._target_series_id:
            if self._target_series_id.startswith("ETF_"):
                cik = self._target_series_id.replace("ETF_", "")
                return {
                    'status': 'success',
                    'method': 'etf_company_fallback',
                    'series_id': self._target_series_id,
                    'cik': int(cik),
                    'original_identifier': self._original_identifier,
                    'message': f"'{self._original_identifier}' resolved as ETF company ticker"
                }
            else:
                return {
                    'status': 'success',
                    'method': 'mutual_fund_lookup',
                    'series_id': self._target_series_id,
                    'original_identifier': self._original_identifier,
                    'message': f"'{self._original_identifier}' resolved as mutual fund ticker"
                }

        # Check if it's a company ticker (ETF) that we didn't resolve
        from edgar.reference.tickers import find_cik
        cik = find_cik(self._original_identifier)

        if cik:
            return {
                'status': 'partial_success',
                'method': 'company_lookup_unresolved',
                'cik': cik,
                'original_identifier': self._original_identifier,
                'message': f"'{self._original_identifier}' found as company ticker but series resolution failed",
                'suggestion': f"Try using CIK {cik} directly: Fund({cik})"
            }

        return {
            'status': 'failed',
            'method': 'no_resolution',
            'original_identifier': self._original_identifier,
            'message': f"'{self._original_identifier}' not found in SEC ticker databases",
            'suggestion': "Verify ticker spelling or try with CIK/series ID directly"
        }

    def list_series(self) -> List[FundSeries]:
        """
        List all fund series associated with this fund.

        If this is a FundCompany, returns all series.
        If this is a FundSeries, returns a list with just this series.
        If this is a FundClass, returns a list with its parent series.

        Returns:
            List of FundSeries instances
        """
        if self._company and hasattr(self._company, 'list_series'):
            return self._company.list_series()

        if self._series:
            return [self._series]

        return []

    def list_classes(self) -> List[FundClass]:
        """
        List all share classes associated with this fund.

        If this is a FundSeries, returns all classes in the series.
        If this is a FundClass, returns a list with just this class.

        Returns:
            List of FundClass instances
        """
        if self._series and hasattr(self._series, 'get_classes'):
            return self._series.get_classes()

        if self._class:
            return [self._class]

        return []

    def __str__(self) -> str:
        return str(self._entity)

    def __repr__(self) -> str:
        return repr(self._entity)

    def __rich__(self):
        """Creates a rich representation of the fund"""
        if hasattr(self._entity, '__rich__'):
            return self._entity.__rich__()
        return str(self)
