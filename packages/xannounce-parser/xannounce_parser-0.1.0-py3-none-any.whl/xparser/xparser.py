# %%
from dataclasses import dataclass
from typing import Literal, cast

from lark import Lark, Transformer, v_args

T_EVENT_TYPE = Literal[
    'New Spot',
    'New Futures',
    'New Margin',
    'Unlisted',
    'Investment Warning',
]

@dataclass
class Coin:
    name: str
    symbol: str

@dataclass
class ParserResult:
    exchange: str
    type: T_EVENT_TYPE
    assets: list[Coin]


title_grammar = r"""
    ?start: upbit_market_support_en
        | upbit_investment_warning_en
        | upbit_unlisted_en

    ?upbit_market_support_en: upbit_market_support_en_1
        | upbit_market_support_en_2
        | upbit_market_support_en_3
        | upbit_market_support_en_4
        

        ?upbit_market_support_en_1: "Market Support for " upbit_asset_list _WHITESPACE* upbit_market? TRAIL?  -> upbit_market_support_en

        ?upbit_market_support_en_2: "Market Support for " symbol_list _WHITESPACE* upbit_market? TRAIL? -> upbit_market_support_en

        ?upbit_market_support_en_3: "New " _LIT_DIGITAL " " _LIT_ASSET "s Added to USDT Market" _WHITESPACE* "(" symbol_list ")" TRAIL? -> upbit_market_support_en
        ?upbit_market_support_en_4: "New " _LIT_DIGITAL " " _LIT_ASSET " on " _true_symbol_list " Market" _WHITESPACE* "(" symbol_list ")" TRAIL? -> upbit_market_support_en

    ?upbit_investment_warning_en: "Investment Warning" " "* "(" NAME ")"  -> upbit_investment_warning_en

    ?upbit_unlisted_en: ubbit_unlisted_en_1
        | ubbit_unlisted_en_2

        ?ubbit_unlisted_en_1: "Notice on Termination of Trading Support for " upbit_asset_list _WHITESPACE* TRAIL? -> upbit_unlisted_en
        ?ubbit_unlisted_en_2: "Termination of market support for " upbit_asset_list _WHITESPACE* TRAIL? -> upbit_unlisted_en


    ?upbit_asset_list: upbit_asset (SEP upbit_asset)* -> asset_list

    ?upbit_asset: NAME "(" NAME ")" -> asset

    ?symbol_list: symbol (SEP symbol)* -> symbol_list
    ?symbol: NAME -> symbol_to_coin

    ?true_symbol_list: true_symbol (SEP true_symbol)* -> symbol_list
    ?true_symbol: TRUE_SYMBOL -> symbol_to_coin
    _true_symbol_list: _TRUE_SYMBOL (_SEP _TRUE_SYMBOL)*

    ?upbit_market: "(" NAME (SEP NAME)* " Market" ")"
    SEP: /,\s*/
    _SEP: SEP
    TRUE_SYMBOL: /[A-Z0-9]+/
    _TRUE_SYMBOL: TRUE_SYMBOL

    NAME: /[A-Za-z0-9](?:[A-Za-z0-9 \-\.]*[A-Za-z0-9])?/
    _WHITESPACE: /\s+/

    _LIT_ASSET: /(a|A)sset/
    _LIT_DIGITAL: /(d|D)igital/

    TRAIL.0: /\s+.*/s
"""

@v_args(inline=True)
class TitleTree(Transformer):
    @staticmethod
    def swap_if_needed(name, symbol):
        '''if name is all upper case and symbol is not, swap them'''
        name = str(name)
        symbol = str(symbol)

        name_is_all_upper = name.upper() == name
        symbol_is_all_upper = symbol.upper() == symbol
        if name_is_all_upper and not symbol_is_all_upper:
            name, symbol = symbol, name

        return name, symbol

    def asset(self, name, symbol) -> Coin:
        name, symbol = self.swap_if_needed(name, symbol)
        return Coin(
            name=str(name),
            symbol=str(symbol),
        )
    def asset_list(self, *args):
        coins = [a for a in args if isinstance(a, Coin)]
        return coins

    def symbol_list(self, *args):
        return [
            i for i in args if isinstance(i, Coin)
        ]
    def symbol_to_coin(self, symbol) -> Coin:
        return Coin(
            name='',
            symbol=str(symbol),
        )

    def upbit_market_support_en(self, assets, *rest):
        return ParserResult(
            exchange='Upbit',
            type='New Spot',
            assets=assets
        )

    def upbit_investment_warning_en(self, symbol, *rest):
        return ParserResult(
            exchange='Upbit',
            type='Investment Warning',
            assets=[Coin(
                name='',
                symbol=str(symbol),
            )]
        )

    def upbit_unlisted_en(self, names, *rest):
        return ParserResult(
            exchange='Upbit',
            type='Unlisted',
            assets=names
        )

def parse_title(title: str) -> ParserResult:
    return cast(ParserResult, title_parser.parse(title))

title_parser = Lark(title_grammar, parser='lalr', transformer=TitleTree())


