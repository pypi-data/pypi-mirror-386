from .._req_builder import _list_dataitem
from ..._common.const import (
    CompanyRelAttributeType as _CompanyRelAttributeType,
    CurrencyTypeWithReportTrade as _CurrencyTypeWithReportTrade
)
from ..._prismcomponent.prismcomponent import _PrismComponent, _PrismDataComponent
from ..._utils import _get_params, _validate_args
from ..._utils.exceptions import PrismValueError


__all__ = [
    "ma",
    "buyback",
    "dataitems",
]


_data_category = __name__.split(".")[-1]


class _PrismTransactionComponent(_PrismDataComponent, _PrismComponent):
    _component_category_repr = _data_category

    @classmethod
    def _dataitems(cls, search : str = None, package : str = None):
        return _list_dataitem(
            datacategoryid=cls.categoryid,
            datacomponentid=cls.componentid,
            search=search,
            package=package,
        )

class ipo(_PrismTransactionComponent):
    """
    | Data pertaining to building an IPO calendar.
    | Default frequency is aperiodic daily.

    Parameters
    ----------
            package : str {'LSEG Street Events'}
                | Desired data package in where the pricing data outputs from.

                .. admonition:: Warning
                    :class: warning

                    If an invalid package is entered without a license, an error will be generated as output.

    Returns
    -------
        prismstudio._PrismComponent

    Examples
    --------
        >>> ipo = ps.transaction.ipo()
        >>> ipo_df = ipo.get_data(startdate='2025-01-01', shownid=['MIC', 'RIC'])
        Data preparation complete
        Downloading: 100%|██████████| 5.97k/5.97k [00:00<00:00, 8.41MB/s]

        >>> ipo_df
        Out[4]:
            listingid       date  offer_amount  ...  form_filed   MIC        RIC
        0     3387552 2025-01-06   204000000.0  ...     17.0000  XNMS    BBNX.OQ
        1     3387922 2025-01-07   140000000.0  ...     17.0000  XNMS    MAZE.OQ
        2     3404241 2025-01-07    14475000.0  ...     14.4518  XKOS  489500.KQ
        3     3387957 2025-01-10   275000000.0  ...     17.0000  XNGS    MTSR.OQ
        4     3395515 2025-01-13   396000000.0  ...     18.0000  XNYS     TTAM.N
        ..        ...        ...           ...  ...         ...   ...        ...
        77    3724826 2025-05-27    28894000.0  ...     29.7697  XTKS     372A.T
        78    3726121 2025-05-29    27480000.0  ...     21.8164  XTKS     373A.T
        79    3727649 2025-06-02    19357000.0  ...     10.3270  XTKS     378A.T
        80    3730228 2025-06-09   153402000.0  ...      5.9446  XSTO   ENITY.ST
        81    3735703 2025-06-15   147564000.0  ...      3.5414  XHKG    6603.HK
        [82 rows x 11 columns]
    """
    @_validate_args
    def __init__(self, package: str = None):
        super().__init__(**_get_params(vars()))


class ma(_PrismTransactionComponent):
    """
    | Get merger and acquisition transaction-related data for equity securities.
    | The default frequency is aperiodic.

    Parameters
    ----------
    dataitemid : int
        Unique identifier for the specific data item.

    target : bool, default True
        Specifies whether the company is a target for an acquisition or an acquirer:
        - If True, the data will be presented from the perspective of a target for an acquisition. This means that given a universe, the data will display all companies that made bids to the companies within the universe.
        - If False, the data will be presented from the perspective of a acquirer for an acquisition. The data will display all companies that the companies in the universe made bids to.

    attribute : str, default 'companyname'
        Desired security attribute identifier to be shown for the counterparty company.

    currency : str, {'report', 'trade', ISO3 currency}, default 'report'
        | Desired currency for the financial data.

        - report : financial reporting currency for a given listing (i.e for Apple - USD, Tencent - CNY)
        - trade : trading currency for a given listing (i.e for Apple - USD, Tencent - HKD)
        - ISO3 currency : desired currency in ISO 4217 format (i.e USD, EUR, JPY, KRW, etc.)

        .. admonition:: Warning
            :class: warning

            | If a selected data item is not a currency value (i.e airplanes owned), the currency input will be ignored.
            | It will behave like parameter input currency=None

    Returns
    -------
    prismstudio._PrismComponent

    Examples
    --------
        >>> ma = ps.transaction.ma(710004, True, 'companyname')
        >>> ps.get_data(ma, 'Korea_primary', '2020-01-01', '2021-01-01')
             listingid        date          value     status   attitude      approach                                   acquirer  currency
        0     20120758  2020-12-17   22177.423520       Open   Friendly   Unsolicited                                        SBW       KRW
        1     20159169  2020-07-10   42698.255104       Paid   Friendly   Unsolicited  GF Financial Industry's No. 1 Corporation       KRW
        2     20159448  2020-03-25   19700.000000       Paid   Friendly   Unsolicited                     Magic Holdings Co.,Ltd       KRW
        3     20166644  2020-01-23   34350.877000  Withdrawn   Friendly   Unsolicited                        GSC. Korea Co.,Ltd.       KRW
        4     20177780  2020-04-13    5846.000000       Paid   Friendly   Unsolicited                      N&F Invesment Union 1       KRW
        ...        ...         ...            ...        ...        ...           ...                                        ...       ...
        210  632312955  2020-01-22  218108.748750       Paid   Friendly     Solicited                           Wintec Co., Ltd.       KRW
        211  636449999  2020-07-08  796474.922456       Paid   Friendly   Unsolicited            Skylake Equity Partners Limited       KRW
        212  643790044  2020-09-18   13792.675000  Withdrawn   Friendly     Solicited                              DAVOLINK Inc.       KRW
        213  671671272  2020-10-26  686100.000000  Withdrawn   Friendly   Unsolicited               Soulbrain Holdings Co., Ltd.       KRW
        214  671671272  2020-12-17  497756.173300       Paid   Friendly   Unsolicited               Soulbrain Holdings Co., Ltd.       KRW
    """

    @_validate_args
    def __init__(
        self,
        dataitemid: int,
        target: bool=True,
        attribute: _CompanyRelAttributeType="companyname",
        currency: _CurrencyTypeWithReportTrade = "report",
        package : str = None,
    ):
        super().__init__(**_get_params(vars()))

    @classmethod
    @_validate_args
    def dataitems(cls, search : str = None, package : str = None):
        return cls._dataitems(search=search, package=package)


class buyback(_PrismTransactionComponent):
    """
    | Get buyback transaction-related data for equity securities.
    | The default frequency is aperiodic.

    Parameters
    ----------
    currency : str, {'report', 'trade', ISO3 currency}, default 'report'
        | Desired currency for the financial data.

        - report : financial reporting currency for a given listing (i.e for Apple - USD, Tencent - CNY)
        - trade : trading currency for a given listing (i.e for Apple - USD, Tencent - HKD)
        - ISO3 currency : desired currency in ISO 4217 format (i.e USD, EUR, JPY, KRW, etc.)

        .. admonition:: Warning
            :class: warning

            | If a selected data item is not a currency value (i.e airplanes owned), the currency input will be ignored.
            | It will behave like parameter input currency=None

    Returns
    -------
    prismstudio._PrismComponent

    Examples
    --------
        >>> buyback = ps.transaction.buyback()
        >>> ps.get_data(buyback, 'Korea_primary', '2020-01-01', '2021-01-01')
             listingid        date    value  currency
        0     20126254  2020-03-16   5000.0       KRW
        1     20130724  2020-03-20  40000.0       KRW
        2     20154597  2020-03-16   3000.0       KRW
        3     20158476  2020-06-18   4000.0       KRW
        4     20158750  2020-03-23    800.0       KRW
        ...        ...         ...      ...       ...
        232  644427262  2020-03-13   1000.0       KRW
        233  652274726  2020-03-30  10000.0       KRW
        234  652868489  2020-03-17   1000.0       KRW
        235  672007118  2020-11-03   1000.0       KRW
        236  675972663  2020-08-14   3000.0       KRW
    """

    @_validate_args
    def __init__(
        self,
        currency: _CurrencyTypeWithReportTrade = "report",
        package : str = None,
    ):
        super().__init__(**_get_params(vars()))

    @classmethod
    @_validate_args
    def dataitems(cls, search : str = None, package : str = None):
        return cls._dataitems(search=search, package=package)


@_validate_args
def dataitems(search: str = None, package: str = None):
    return _list_dataitem(
            datacategoryid=_PrismTransactionComponent.categoryid,
            datacomponentid=None,
            search=search,
            package=package,
        )