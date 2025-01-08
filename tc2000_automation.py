import win32clipboard
import pyautogui
import time

class TC2000Automation:
    def __init__(self):
        self.last_symbol = None
        
    def get_clipboard_content(self):
        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData()
        except:
            data = ""
        win32clipboard.CloseClipboard()
        return data.strip()
    
    def chart_symbol(self, symbol):
        # Press F2 to focus TC2000 symbol input
        pyautogui.press('f2')
        time.sleep(0.1)
        
        # Type symbol and press enter
        pyautogui.write(symbol)
        pyautogui.press('enter')
        
    def monitor_clipboard(self):
        print("Monitoring clipboard for symbols...")
        while True:
            symbol = self.get_clipboard_content()
            if symbol and symbol != self.last_symbol:
                self.chart_symbol(symbol)
                self.last_symbol = symbol
            time.sleep(0.1)

if __name__ == "__main__":
    automation = TC2000Automation()
    automation.monitor_clipboard()