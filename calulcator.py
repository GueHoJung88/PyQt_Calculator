import sys
import re
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6 import QtGui
from PyQt6.QtCore import *

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

from_class = uic.loadUiType("calculator.ui")[0]

class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.calculation_formula:str = "0"
        self.result_value:str = "0.0"
        self.parenthesis_cnt = 0
        self.view_formula_operators = ["+","-","×", "÷"]
        self.is_sign_reversed = False

        # INIT CAL TEXT EDIT
        self.calEdit.setText(self.calculation_formula)
        self.calEdit.setAlignment(Qt.AlignmentFlag.AlignRight)

        # INIT RESULT TEXT EDIT
        self.resultEdit.setText(self.result_value)
        self.resultEdit.setAlignment(Qt.AlignmentFlag.AlignRight)

        # INIT CLEAR ALL, CLEAR ENTRY
        self.btn_clear_all.clicked.connect(self.clear)
        self.btn_clear_entry.clicked.connect(lambda: self.clear(amount=1))

        # INIT NUMBER BUTTONS
        self.btn_zero.clicked.connect(lambda: self.appendNumber(number=Singledigit.ZERO.value))
        self.btn_one.clicked.connect(lambda: self.appendNumber(number=Singledigit.ONE.value))
        self.btn_two.clicked.connect(lambda: self.appendNumber(number=Singledigit.TWO.value))
        self.btn_three.clicked.connect(lambda: self.appendNumber(number=Singledigit.THREE.value))
        self.btn_four.clicked.connect(lambda: self.appendNumber(number=Singledigit.FOUR.value))
        self.btn_five.clicked.connect(lambda: self.appendNumber(number=Singledigit.FIVE.value))
        self.btn_six.clicked.connect(lambda: self.appendNumber(number=Singledigit.SIX.value))
        self.btn_seven.clicked.connect(lambda: self.appendNumber(number=Singledigit.SEVEN.value))
        self.btn_eight.clicked.connect(lambda: self.appendNumber(number=Singledigit.EIGHT.value))
        self.btn_nine.clicked.connect(lambda: self.appendNumber(number=Singledigit.NINE.value))

        # DECIMAL POINTER
        self.btn_decimal_point.clicked.connect(lambda: self.appendDecimalPoint(formula_str=self.calculation_formula))

        # INIT OPERATORS
        self.btn_equals.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.EQUALS))
        self.btn_plus.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.PLUS))
        self.btn_minus.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.MINUS))
        self.btn_multiply.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.MULTIPLY))
        self.btn_devide.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.DEVIDE))
        self.btn_parenthesis_start.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.PARENTHESIS_START))
        self.btn_parenthesis_end.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.PARENTHESIS_END))
        self.btn_parenthesis_end.setEnabled(False)

        # INIT REVERSING SIGN
        self.btn_positive_negative.clicked.connect(self.reversingSign)


    def reversingSign(self):
        if self.is_sign_reversed:
            reversed_str = self.calculation_formula[2:-1]
        else:
            reversed_str = f"-({self.calculation_formula})" 
        self.is_sign_reversed = not self.is_sign_reversed
        self.calculation_formula = reversed_str
        self.setCalText()
        
    def setResultText(self):
        print(f"setResultText : {self.result_value}")
        try:
            num = float(self.result_value)
            self.resultEdit.setText(format(num, ','))
        except ValueError as e:
            self.resultEdit.setText(str(self.result_value))
        self.resultEdit.setAlignment(Qt.AlignmentFlag.AlignRight)

    def setCalText(self, param:str=""):
        if param == "":
            pass
            # self.calEdit.setText(self.calculation_formula)
        else :
            if type(param) == str:
                self.calculation_formula += param
            else :
                self.calculation_formula += str(param)
        
        self.calEdit.setText(self.calculation_formula)
        self.calEdit.setAlignment(Qt.AlignmentFlag.AlignRight) 
        self.calEdit.moveCursor(QTextCursor.MoveOperation.End)

        self.activateSign()

    def appendDecimalPoint(self, formula_str:str):
        self.is_sign_reversed = False
        last_char = self.getLastChar(formula_str)
        if last_char.isdigit():
            numbers = re.findall(r'\d+\.\d+|\d+', formula_str)
            length = len(numbers)
            last_digit = str(numbers[length-1])
            print(f"appendDecimalPoint : {last_digit}")

            if last_digit.__contains__("."):
                pass
            else:
                self.calculation_formula += "."
        else:
            if not last_char.endswith("."):
                if last_char.endswith(")"):
                    self.calculation_formula = self.genDefaultOperator(self.calculation_formula, parenthesis_end=")")
                    self.calculation_formula += "0."
                else:
                    self.calculation_formula += "0."

        self.setCalText()
        

    def appendNumber(self, number:int):
        self.is_sign_reversed = False
        self.calculation_formula = self.genDefaultOperator(self.calculation_formula, parenthesis_end=")")
        if self.calculation_formula == "0":
            if number == 0:
                self.calculation_formula = "0"
            else:
                self.calculation_formula = str(number)
        else:
            self.calculation_formula += str(number)
        self.setCalText()

    def clear(self, amount:int=0):
        self.is_sign_reversed = False
        if amount == 0:
            self.calculation_formula = "0"
            self.result_value = "0"
            self.parenthesis_cnt = 0
            self.setResultText()
        else :
            if len(self.calculation_formula) == 1  and self.calculation_formula.isdigit():
                self.calculation_formula = "0"
            else:
                self.calculation_formula = self.calculation_formula[:-1]
                self.countParenthesis(self.calculation_formula)
        self.setCalText()
        self.activateEndParenthesis()
        self.activateEquals()

    def countParenthesis(self, counting_str:str):
        self.parenthesis_cnt = counting_str.count("(") - counting_str.count(")")

    def eaCalculate(self, operate_type:int):
        match operate_type:
            case EaOperator.EQUALS:
                print("EaOperator EQUALS")

                rplcd_str = self.genEvalStr(self.calculation_formula)
                try:
                    self.result_value = eval(rplcd_str)
                    print(f"self.result_value : {self.result_value}")
                except Exception as e: # Catches any other exception
                    print(f"An unexpected error occurred: {e}")

                # Append Operator on Formula

                self.setResultText()
            case EaOperator.PLUS:
                print("EaOperator PLUS")
                self.is_sign_reversed = False
                # Append Operator on Formula
                self.calculation_formula = self.genFormulaStr("+")
            case EaOperator.MINUS:
                print("EaOperator MINUS")
                self.is_sign_reversed = False
                # Append Operator on Formula
                self.calculation_formula = self.genFormulaStr("-")
            case EaOperator.MULTIPLY:
                print("EaOperator MULTIPLY")
                self.is_sign_reversed = False
                # Append Operator on Formula
                self.calculation_formula = self.genFormulaStr("×")
            case EaOperator.DEVIDE:
                print("EaOperator DEVIDE")
                self.is_sign_reversed = False
                # Append Operator on Formula
                self.calculation_formula = self.genFormulaStr("÷")
            case EaOperator.PARENTHESIS_START:
                print("EaOperator PARENTHESIS_START")
                self.is_sign_reversed = False
                self.parenthesis_cnt += 1
                self.activateEndParenthesis()
                self.activateEquals()
                # Append Operator on Formula
                if self.calculation_formula == "0":
                    self.calculation_formula = "("
                else:
                    self.calculation_formula = self.genDefaultOperator(self.calculation_formula, "(")
            case EaOperator.PARENTHESIS_END:
                print("EaOperator PARENTHESIS_END")
                self.is_sign_reversed = False
                self.parenthesis_cnt -= 1
                self.activateEndParenthesis()
                self.activateEquals()
                # Append Operator on Formula
                self.calculation_formula += ")"
            case _:
                print("Something's wrong with the operator")
        self.setCalText()

    def genEvalStr(self, formula_str):
        view_operators = ["×", "÷"]
        py_operators = ['*','/']

        for idx, v_oprt in enumerate(view_operators):
            print(f"idx : {idx}, v_oprt : {v_oprt}, py_operators[{idx}] : {py_operators[idx]}")
            formula_str = formula_str.replace(v_oprt, py_operators[idx])
        
        formula_str = self.manageEmptyValue(formula_str)
        return formula_str
    
    def genFormulaStr(self, ea_operator):
        for oprt in self.view_formula_operators:
            if self.calculation_formula.endswith(oprt):
                self.calculation_formula = self.calculation_formula[:-1]
                break

        self.calculation_formula += ea_operator
        self.calculation_formula = self.manageEmptyValue(self.calculation_formula)
        return self.calculation_formula

    def genDefaultOperator(self, formula_str:str, parenthesis_start:str="", parenthesis_end:str="", ):
        last_char = self.getLastChar(formula_str)

        if parenthesis_start == "(":
            if last_char.isdigit() or last_char == "." or last_char == ")":
                formula_str = formula_str.replace(".","")
                formula_str += "×"
            
            formula_str += parenthesis_start

        if parenthesis_end == ")" and last_char == ")":
            formula_str +=  "×"

        return formula_str

    def getLastChar(self, formula_str):
        str_len = len(formula_str)
        last_char = formula_str[str_len-1:str_len]
        return last_char

    def manageEmptyValue(self, formula_str:str):
        formula_str = formula_str.replace("()", "(0)")
        return formula_str

    def activateEndParenthesis(self):
        if self.parenthesis_cnt == 0:
            self.btn_parenthesis_end.setEnabled(False)
        else:
            self.btn_parenthesis_end.setEnabled(True)
        
    def activateEquals(self):
        if self.parenthesis_cnt == 0:
            self.btn_equals.setEnabled(True)
        else:
            self.btn_equals.setEnabled(False)

    def activateSign(self):
        check_points = ['operator', 'parenthesis']

        for chck_point in check_points:
            match chck_point:
                case 'operator':
                    last_char = self.getLastChar(self.calculation_formula)
                    if self.view_formula_operators.__contains__(last_char) or last_char == ".":
                        self.btn_positive_negative.setEnabled(False)
                        break
                    else :
                        self.btn_positive_negative.setEnabled(True)
                    
                case 'parenthesis':
                    if self.parenthesis_cnt == 0:
                        self.btn_positive_negative.setEnabled(True)
                    else:
                        self.btn_positive_negative.setEnabled(False)
                        break

        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()
    sys.exit(app.exec())