def calculate_sum(a, b):
    """
    Calculates the sum of two inputs using the '+' operator.

    This function adds two inputs 'a' and 'b'. The behavior depends on the types
    of 'a' and 'b'. For numerical types (int, float), it performs arithmetic
    addition. For strings, it performs concatenation.

    Args:
        a (int | float | str): The first input.
        b (int | float | str): The second input.

    Returns:
        int | float | str: The result of 'a + b'. The type of the return value
                           depends on the types of 'a' and 'b'.

    Raises:
        TypeError: If 'a' and 'b' are of incompatible types for the '+' operator
                   (e.g., adding an int to a str).
    """
    return a + b