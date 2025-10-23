# Module Name: concrete/strategies.py
# Description: This modul contains concrete strategy classes.
# Author: (wattleflow@outlook.com)
# Copyright: (c) 2022-2025 WattleFlow
# License: Apache 2 Licence


from abc import abstractmethod, ABC
from logging import Handler, NOTSET
from typing import Optional
from wattleflow.core import IWattleflow, IStrategy, ITarget
from wattleflow.concrete import AuditLogger


# Generic strategy
class Strategy(IStrategy, AuditLogger, ABC):
    def __init__(
        self,
        level: int = NOTSET,
        handler: Optional[Handler] = None,
    ):
        self._level: int = level
        self._handler: Optional[Handler] = handler

        IStrategy.__init__(self)
        AuditLogger.__init__(self, level=level, handler=handler, logger=None)

    @abstractmethod
    def execute(self, caller: IWattleflow, *args, **kwargs) -> Optional[ITarget]:
        pass

    def __repr__(self) -> str:
        return f"{self.name}"


class StrategyGenerate(Strategy, ABC):
    def generate(self, caller: IWattleflow, *args, **kwargs) -> Optional[ITarget]:
        return self.execute(caller, *args, **kwargs)


class StrategyCreate(Strategy, ABC):
    def create(self, caller: IWattleflow, *args, **kwargs) -> Optional[ITarget]:
        return self.execute(caller=caller, *args, **kwargs)


class StrategyRead(Strategy, ABC):
    def read(
        self,
        caller: IWattleflow,
        identifier: str,
        *args,
        **kwargs,
    ) -> Optional[ITarget]:
        return self.execute(caller=caller, identifier=identifier, *args, **kwargs)


class StrategyWrite(Strategy, ABC):
    def write(self, caller: IWattleflow, document: ITarget, *args, **kwargs) -> bool:
        if self.execute(caller=caller, document=document, *args, **kwargs) is None:
            return False
        return True
