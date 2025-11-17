class Calculator:
    def __init__(self):
        self.current = ""
        self.result = 0
        self.new_number = True
        self.last_operation = None

    def number_press(self, number):
        if self.new_number:
            self.current = str(number)
            self.new_number = False
        else:
            self.current += str(number)
        return self.current

    def operation_press(self, operation):
        if self.current:
            if not self.new_number:
                self.calculate()
                self.new_number = True
            self.last_operation = operation
        return str(self.result)

    def calculate(self):
        if self.last_operation:
            try:
                current = float(self.current)
                if self.last_operation == "+":
                    self.result += current
                elif self.last_operation == "-":
                    self.result -= current
                elif self.last_operation == "*":
                    self.result *= current
                elif self.last_operation == "/":
                    if current == 0:
                        self.result = "错误：除数不能为0"
                        return
                    self.result /= current
            except ValueError:
                self.result = "错误"
        else:
            try:
                self.result = float(self.current)
            except ValueError:
                self.result = "错误"

    def clear(self):
        self.current = ""
        self.result = 0
        self.new_number = True
        self.last_operation = None
        return "0"

    def get_result(self):
        self.calculate()
        self.new_number = True
        self.last_operation = None
        return str(self.result)
