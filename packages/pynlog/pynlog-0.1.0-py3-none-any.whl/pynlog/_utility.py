from inspect import currentframe


def truncate(string: str, max_len: int = 24) -> str:
    """
    Truncates a string to a maximum length, padding with spaces if necessary.

    This function ensures that the resulting string is exactly `max_len` characters long.
    - If the input string is shorter than `max_len`, it's padded with spaces on the right.
    - If the input string is longer than `max_len`, it's truncated.

    Example Output:
        ...y_very_very_long_name
        short_name

    Args:
        string (str): The string to truncate or pad.
        max_len (int): The maximum length of the resulting string. Defaults to 24.
    
    Returns:
        str: The truncated or padded string.
    """
    if (len(string) <= max_len):
        return string.ljust(max_len)
    return "..." + string[-(max_len - 3):]


def get_caller(n: int = 3) -> str:
    """
    Retrieves the name of the calling function (and potentially its class) from the call stack.

    This function traverses the call stack to identify the caller of the current function.
    It returns a formatted string representing the caller's name, including the class name if available.

    Example Output:
        myclass.myfunction
    
    Args:
        n (int): The number of frames to go back in the call stack to reach the caller. Defaults to 3.
    
    Returns:
        str: A formatted string representing the caller's name, potentially including the class name.
    """
    frame = currentframe()
    for _ in range(n):
        if not frame:
            return ""
        frame = frame.f_back
    
    if not frame or not frame.f_code:
        return ""
    
    func_name = frame.f_code.co_name    
    cls_name = None
    if "self" in frame.f_locals:
        cls_name = frame.f_locals["self"].__class__.__name__
    elif "cls" in frame.f_locals:
        cls_name = frame.f_locals["cls"].__name__
    
    if cls_name:
        return truncate(f"{cls_name}.{func_name}")
    return truncate(func_name)
