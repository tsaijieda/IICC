"""戰術板 → 戰術語言轉譯。"""

from .io import board_from_dict, load_board, result_to_dict, write_result_yaml
from .models import BoardInput, TouchRecord, TranslationResult
from .translator import translate_board

__all__ = [
    "BoardInput",
    "TouchRecord",
    "TranslationResult",
    "board_from_dict",
    "load_board",
    "result_to_dict",
    "translate_board",
    "write_result_yaml",
]
