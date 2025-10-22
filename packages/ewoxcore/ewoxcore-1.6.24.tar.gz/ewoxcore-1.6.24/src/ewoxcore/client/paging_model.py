from typing import Any, Callable, Generic, List, Dict, Text, Optional, Tuple, Union, TypeVar, Type
from ewoxcore.decorators.serializable import Serializable

T = TypeVar("T")

@Serializable
class PagingModel():
    def __init__(self, rows:list[T], numRows:int, skip:int, num:int, numInTabs:list[int]) -> None:
        self.rows: list[T] = rows
        self.numRows: int = numRows
        self.skip: int = skip
        self.num: int = num
        self.numInTabs: list[int] = numInTabs
