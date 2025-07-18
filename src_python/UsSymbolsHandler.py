from src_python.ChaseHoundBase import ChaseHoundBase


class UsSymbolsHandler(ChaseHoundBase):
    def __init__(self):
        super().__init__()

    def get_nasdaq_symbols(self) -> List[str]:
        pass