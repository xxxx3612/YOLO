import tkinter as tk
from calculator import Calculator

class CalculatorUI:
    def __init__(self, root):
        self.root = root
        self.calculator = Calculator()
        self.root.title("简单计算器")
        
        # 创建显示器
        self.display = tk.Entry(root, width=20, font=('Arial', 20), justify='right')
        self.display.insert(0, '0')
        self.display.grid(row=0, column=0, columnspan=4, padx=5, pady=5)
        self.display.config(state='readonly')

        # 按钮文本和位置
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            'C', '0', '=', '+'
        ]

        # 创建按钮
        row = 1
        col = 0
        for button in buttons:
            cmd = lambda x=button: self.click(x)
            tk.Button(root, text=button, width=5, height=2,
                     font=('Arial', 14), command=cmd).grid(row=row, column=col)
            col += 1
            if col > 3:
                col = 0
                row += 1

    def click(self, key):
        if key in '0123456789':
            display_text = self.calculator.number_press(key)
        elif key in '+-*/':
            display_text = self.calculator.operation_press(key)
        elif key == '=':
            display_text = self.calculator.get_result()
        elif key == 'C':
            display_text = self.calculator.clear()
            
        # 更新显示
        self.display.config(state='normal')
        self.display.delete(0, tk.END)
        self.display.insert(0, display_text)
        self.display.config(state='readonly')

def main():
    root = tk.Tk()
    calculator = CalculatorUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()