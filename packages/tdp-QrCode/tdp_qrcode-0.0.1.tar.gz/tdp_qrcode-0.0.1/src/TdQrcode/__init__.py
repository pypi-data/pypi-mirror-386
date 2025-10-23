'''Info Header Start
Name : __init__
Author : Wieland PlusPlusOne@AMB-ZEPH15
Saveorigin : Project.toe
Saveversion : 2023.12000
Info Header End'''

from pathlib import Path
ToxFile = Path( Path(  __file__ ).parent, "TdQrcode.tox" )

from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from .extTdQrCode import extTdQrCode
    Typing = Union[
        extTdQrCode
    ]
else:
    Typing = None

__all__ = ["ToxFile", "Typing"]