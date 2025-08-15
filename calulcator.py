import sys
import re
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from PyQt6 import QtGui
from PyQt6.QtCore import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage  # triggerAction용

QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)

from enum import Enum

class EaOperator(Enum):
    EQUALS = 0
    PLUS = 1
    MINUS = 2
    MULTIPLY = 3
    divide = 4
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

        # print(f"styleSheet() : {self.btn_zero.style}")

        # DECIMAL POINTER
        self.btn_decimal_point.clicked.connect(lambda: self.appendDecimalPoint(formula_str=self.calculation_formula))

        # INIT OPERATORS
        self.btn_equals.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.EQUALS))
        self.btn_plus.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.PLUS))
        self.btn_minus.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.MINUS))
        self.btn_multiply.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.MULTIPLY))
        self.btn_divide.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.divide))
        self.btn_parenthesis_start.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.PARENTHESIS_START))
        self.btn_parenthesis_end.clicked.connect(lambda: self.eaCalculate(operate_type=EaOperator.PARENTHESIS_END))
        self.btn_parenthesis_end.setEnabled(False)

        # INIT PPAP
        # self.btn_ppap.clicked.connect(self.callPPAP)

        # INIT REVERSING SIGN
        self.btn_positive_negative.clicked.connect(self.reversingSign)

         # ---------- (A) WebEngine 워밍업: data: URL 로 매우 가벼운 페이지 로드 ----------
        self._warm_view = QWebEngineView()
        self._warm_view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        self._warm_view.resize(1, 1)
        # data: URL 로드 → QtWebEngineProcess 선기동(첫 렌더링 깜빡임 완화)
        QTimer.singleShot(
            0,
            lambda: self._warm_view.setUrl(
                QUrl("data:text/html;charset=utf-8,%3C!DOCTYPE%20html%3E%3Chtml%3E%3C/head%3E%3Cbody%3E%3C/body%3E%3C/html%3E")
            ),
        )

        # ---------- 재사용할 영상 다이얼로그/뷰 준비 ----------
        self._video_dialog = QDialog(self)
        self._video_dialog.setWindowTitle("Why dividing by zero is undefined")
        # show()로도 모달 동작을 원하면 ApplicationModal 설정
        self._video_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)

        vbox = QVBoxLayout(self._video_dialog)
        self._video_view = QWebEngineView(self._video_dialog)
        vbox.addWidget(self._video_view)
        self._video_dialog.resize(420, 620)

        # 상태 플래그
        self._is_preloading = False      # 지금 '사전 로드' 중인지
        self._preloaded_once = False     # 최소 1회 프리로드 완료했는지
        self._pending_show = False       # loadFinished 후 보여줄지 큐 상태

        # loadFinished 통합 핸들러: 필요할 때만 show()
        def _on_load_finished(ok: bool):
            # 프리로드 1회 완료 마크
            if self._is_preloading:
                self._preloaded_once = True
                self._is_preloading = False
            # 표시 예약이 걸려 있으면, 로드 완료 직후에 부드럽게 보여줌
            if self._pending_show:
                self._video_dialog.show()
                self._video_dialog.raise_()
                self._video_dialog.activateWindow()
                self._pending_show = False

        self._video_view.loadFinished.connect(_on_load_finished)

        # ---------- (B) 앱 시작 직후, 유튜브 임베드를 백그라운드 프리로드 ----------
        # autoplay=0, mute=1 → 소리/재생 없이 캐시와 초기화만 미리 완료
        self._yt_video_id = "3weRI66g36o"  # 원하는 영상 ID로 교체 가능
        preload_url = QUrl(
            f"https://www.youtube.com/embed/{self._yt_video_id}"
            "?autoplay=0&mute=1&rel=0&enablejsapi=1"  # 가볍고 조용하게 미리 로드
        )
        def _start_preload():
            self._is_preloading = True
            # 다이얼로그는 보이지 않은 상태에서 조용히 로드만 수행
            self._video_dialog.hide()
            self._video_view.setUrl(preload_url)

        # 이벤트 루프가 돈 뒤, 아주 살짝 있다가 시작(워밍업 직후 프리로드)
        QTimer.singleShot(5, _start_preload)

        # 팝업이 닫히는 모든 경로(닫기 버튼, ESC, 프로그램 종료 등)에 대응
        # self._video_dialog.finished.connect(lambda _: self._stop_video())
        self._video_dialog.finished.connect(lambda _: self._on_video_dialog_closed())
        self._video_dialog.rejected.connect(self._stop_video)

        # (선택) 사용자가 타이틀바 X로 닫을 때도 확실히 처리하고 싶으면:
        orig_close = self._video_dialog.closeEvent
        def _close_evt(e):
            self._stop_video()
            if orig_close:
                orig_close(e)
            else:
                e.accept()
        self._video_dialog.closeEvent = _close_evt

    # --- WindowClass 메서드로 추가 ---
    def _stop_video(self):
        """팝업 종료 시 유튜브 재생을 완전히 멈추고 리소스를 정리합니다."""
        try:
            # 네트워크 로딩/스트리밍 중이면 중단
            self._video_view.page().triggerAction(QWebEnginePage.WebAction.Stop)
        except Exception:
            pass
        # 혹시 모를 잔여 오디오 차단
        try:
            self._video_view.page().setAudioMuted(True)
        except Exception:
            pass
        # 빈 문서로 전환(다음 재생 시 정상적으로 setUrl 하면 다시 재생됨)
        self._video_view.setUrl(QUrl("about:blank"))

    def _on_video_dialog_closed(self):
        # 재생 중지(이미 구현되어 있으면 그대로 호출)
        try:
            self._stop_video()
        except Exception:
            pass

        # 원하는 후처리
        try:
            self.clear(amount=1)        # ← 여기서 원하는 함수 호출
            self.result_value = "0"
            self.setResultText()
        except Exception:
            pass

    # ---------- (C) 실제 호출: 부드럽게 show() + 필요 시에만 autoplay=1로 빠르게 재로드 ----------
    def callYTBE(self):
        # 사용자 경험상, 표시 동작을 로드 완료 직후 수행하도록 예약
        self._pending_show = True

        # 이미 프리로드가 끝났다면 'autoplay=1'로 짧게 재로드 → 즉시 표시(깜빡임 최소)
        play_url = QUrl(
            f"https://www.youtube.com/embed/{self._yt_video_id}"
            # mute 파라미터는 기기 정책에 따라 필요할 수 있음(autoplay 제한 회피용)
            "?autoplay=1&rel=0"
        )

        # 다이얼로그를 잠시 숨긴 뒤 새 URL 적용 → loadFinished에서 자연스럽게 show()
        self._video_dialog.hide()
        self._video_view.setUrl(play_url)
        self._video_view.page().setAudioMuted(False)

        # 만약 네트워크/정책으로 autoplay가 막히면, 사용자가 클릭해서 재생할 수 있도록 컨트롤 제공됨.
        # (필요 시 controls=1, modestbranding=1 등의 파라미터를 추가하세요.)

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
        self.activateEndParenthesis()
        self.manageEmptyValue(self.calculation_formula)

    def appendDecimalPoint(self, formula_str:str):
        self.is_sign_reversed = False
        last_char = self.getLastChar(formula_str)
        if last_char.isdigit():
            last_digit = self.getLastNumber(formula_str)

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
        last_char_l_shifted = self.getLastChar(self.calculation_formula, l_shift=1)
        last_number = self.getLastNumber(self.calculation_formula)
        print(f"appendNumber last_char_l_shifted : {last_char_l_shifted}, last_number : {last_number}")
        if self.calculation_formula == "0":
            if number == 0:
                self.calculation_formula = "0"
            else:
                self.calculation_formula = str(number)
        elif (last_char_l_shifted == "(" or self.view_formula_operators.__contains__(last_char_l_shifted)) and last_number == "0":
            self.calculation_formula = (self.calculation_formula[:-1] + str(number))
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
        last_char = self.getLastChar(self.calculation_formula)
        self.calculation_formula = self.manageDecimalPointForOperator(self.calculation_formula, last_char)
        match operate_type:
            case EaOperator.EQUALS:
                print("EaOperator EQUALS")
                self.calculation_formula = self.manageLastOperator(self.calculation_formula)
                rplcd_str = self.genEvalStr(self.calculation_formula)
                try:
                    self.result_value = eval(rplcd_str)
                    print(f"self.result_value : {self.result_value}")
                except Exception as e: # Catches any other exception
                    print(f"An unexpected error occurred: {e}")
                    if str(e) == "division by zero":
                        self.result_value = f"Error : {str(e)}"
                        self.setResultText()
                        self.callYTBE()

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
            case EaOperator.divide:
                print("EaOperator divide")
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

        formula_str = self.manageLastOperator(formula_str)

        for idx, v_oprt in enumerate(view_operators):
            print(f"idx : {idx}, v_oprt : {v_oprt}, py_operators[{idx}] : {py_operators[idx]}")
            formula_str = formula_str.replace(v_oprt, py_operators[idx])
        
        formula_str = self.manageEmptyValue(formula_str)
        
        return formula_str

    def manageLastOperator(self, formula_str):
        last_char = self.getLastChar(formula_str)
        if self.view_formula_operators.__contains__(last_char):
            formula_str = formula_str[:-1]
        return formula_str
    
    def genFormulaStr(self, ea_operator):
        for oprt in self.view_formula_operators:
            if self.calculation_formula.endswith(oprt):
                self.calculation_formula = self.calculation_formula[:-1]
                break
        
        last_char = self.getLastChar(self.calculation_formula)
        if last_char == "(":
            self.calculation_formula += "0"
        self.calculation_formula += ea_operator
        self.calculation_formula = self.manageEmptyValue(self.calculation_formula)
        return self.calculation_formula

    def genDefaultOperator(self, formula_str:str, parenthesis_start:str="", parenthesis_end:str="", ):
        last_char = self.getLastChar(formula_str)

        if parenthesis_start == "(":
            if last_char.isdigit() or last_char == ")":
                formula_str += "×"
            
            formula_str += parenthesis_start

        if parenthesis_end == ")" and last_char == ")":
            formula_str +=  "×"

        return formula_str

    def manageDecimalPointForOperator(self, formula_str, last_char):
        if last_char == "." :
            formula_str = formula_str[:-1]
        return formula_str

    def getLastChar(self, formula_str, l_shift:int=0):
        str_len = len(formula_str)
        last_char = formula_str[str_len-1-l_shift:str_len-l_shift]
        return last_char
    
    def checkIfFloat(self, formula_str):
        rgex = r'\d+\.\d+'
        f_number = re.findall(rgex, formula_str)
        length = len(f_number)
        last_float = str(f_number[length-1])
        print(f"last_float : {last_float}")
        return last_float
    
    def getLastNumber(self, formula_str, only_int:bool=False):
        if only_int:
            rgex = r'\d+'
        else :
            rgex = r'\d+\.\d+|\d+'
        numbers = re.findall(rgex, formula_str)
        length = len(numbers)
        last_digit = str(numbers[length-1])
        print(f"getLastNumber : {last_digit}")
        return last_digit

    def manageEmptyValue(self, formula_str:str):
        formula_str = formula_str.replace("()", "(0)")
        return formula_str

    def activateEndParenthesis(self):
        last_char = self.getLastChar(self.calculation_formula)
        if self.view_formula_operators.__contains__(last_char):
            self.btn_parenthesis_end.setEnabled(False)
        else:
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

        

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     myWindows = WindowClass()
#     myWindows.show()
#     sys.exit(app.exec())

# --- __main__ 블록 교체 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    win = WindowClass()  # <-- 여기서 바로 show() 하지 않습니다!

    # 1) QtWebEngine 사전 기동(백그라운드, 화면 미표시)
    warm_view = QWebEngineView()
    warm_view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    warm_view.resize(1, 1)

    shown = {"done": False}
    def show_main():
        if not shown["done"]:
            shown["done"] = True
            win.show()  # 워밍업이 끝났거나 타임아웃이 오면 그때 최초 1회 표시

    # 워밍업 완료 → 다음 틱에서 메인창 표시
    warm_view.loadFinished.connect(lambda ok: QTimer.singleShot(0, show_main))
    warm_view.setUrl(QUrl("data:text/html;charset=utf-8,<html></html>"))

    # 2) 예외 상황 대비: 1.5초 안에 신호가 없으면 그래도 한번 보여줌
    QTimer.singleShot(1500, show_main)

    sys.exit(app.exec())