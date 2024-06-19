def is_number(s):
    """
    判断一个字符串是否为数字（整数或浮点数）。
    包含正负号和小数点的情况。
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def format_to_two_places(value):
    return float(f"{value:.2f}")


def format_to_integer(value):
    return int(value)

def format_currency(value):
    try:
        # 确保传递给该函数的值是整数
        value = int(value)
        formatted_value = "{:,}".format(value)
        return formatted_value
    except Exception as e:
        print(f"Error formatting currency: {e}")
        return str(value)  # 返回原始值，以防止显示问题#
