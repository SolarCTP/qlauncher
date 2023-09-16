class State:
    def __init__(self, **kwargs) -> None:
        for arg, val in kwargs.items():
            self.__setattr__(arg, val)