from enum import Enum

class EaOperator(Enum):
    EQUALS = 0
    PLUS = 1
    MINUS = 2
    MULTIPLY = 3
    DEVIDE = 4
    PARENTHESIS_START = 5
    PARENTHESIS_END = 6

class Singledigit(Enum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9

class ElementrArithmatic():
    
    def __init__(self):
        super().__init__()

    def eaPlus(self, prev_val, val):
        prev_val = eval(prev_val)
        return eval(f"{prev_val}+{val}")
    
    def eaMinus(self, prev_val, val):
        prev_val = eval(prev_val)
        return eval(f"{prev_val}-{val}")
    
    def eaMultiply(self, prev_val, val):
        prev_val = eval(prev_val)
        return eval(f"{prev_val}*{val}")
    
    def eaDevide(self, prev_val, val):
        prev_val = eval(prev_val)
        return eval(f"{prev_val}/{val}")