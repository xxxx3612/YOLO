def calculator():
    print("简单计算器")
    print("1. 加法")
    print("2. 减法")
    print("3. 乘法")
    print("4. 除法")
    print("5. 退出")
    
    while True:
        choice = input("请选择操作(1-5): ")
        
        if choice == '5':
            print("感谢使用！")
            break
            
        if choice in ('1', '2', '3', '4'):
            num1 = float(input("请输入第一个数字: "))
            num2 = float(input("请输入第二个数字: "))
            
            if choice == '1':
                print(f"{num1} + {num2} = {num1 + num2}")
            elif choice == '2':
                print(f"{num1} - {num2} = {num1 - num2}")
            elif choice == '3':
                print(f"{num1} * {num2} = {num1 * num2}")
            elif choice == '4':
                if num2 == 0:
                    print("错误：除数不能为0！")
                else:
                    print(f"{num1} / {num2} = {num1 / num2}")
        else:
            print("无效的选择！请重新输入。")

if __name__ == "__main__":
    calculator()