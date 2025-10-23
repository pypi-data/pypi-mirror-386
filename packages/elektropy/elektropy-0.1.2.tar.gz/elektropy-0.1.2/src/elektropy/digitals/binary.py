def binary_to_decimal(binary_str: str) -> int:
    """
    Convert a binary string to a decimal integer.

    :param binary_str: A string representing a binary number (e.g., '1011').
    :return: The decimal integer equivalent of the binary string.
    """

    return int(binary_str, base=2)

def decimal_to_binary(decimal_int: int) -> str:
    """
    Convert a decimal integer to a binary string.

    :param decimal_int: An integer representing a decimal number (e.g., 11).
    :return: The binary string equivalent of the decimal integer (e.g., '1011').
    """
    return bin(decimal_int)[2:]  

def twos_comp_to_decimal(binary_str: str) -> int:
    """
    Convert a binary string in 2's complement to a decimal integer.

    :param binary_str: A string representing a binary number in 2's complement (e.g., '1011' for -5 in 4-bit).
    :return: The decimal integer equivalent of the 2's complement binary string.
    """
    num_bits = len(binary_str)
    decimal = int(binary_str, 2)
    
    # If the leftmost bit is 1, it's a negative number
    if binary_str[0] == '1':
        decimal = decimal - (1 << num_bits)
    
    return decimal

def decimal_to_twos_comp(decimal_int: int, num_bits: int) -> str:
    """
    Convert a decimal integer to a binary string in 2's complement.

    :param decimal_int: An integer to convert (can be positive or negative).
    :param num_bits: Number of bits to use in the representation.
    :return: The 2's complement binary string.
    :raises ValueError: If the number cannot be represented in the given bits.
    """
    if decimal_int >= 0:
        if decimal_int >= (1 << (num_bits - 1)):
            raise ValueError(f"Number too large for {num_bits}-bit representation")
        binary = bin(decimal_int)[2:].zfill(num_bits)
    else:
        if decimal_int < -(1 << (num_bits - 1)):
            raise ValueError(f"Number too small for {num_bits}-bit representation")
        # Add 2^n to negative numbers
        binary = bin((1 << num_bits) + decimal_int)[2:]
    
    return binary

def binary_to_hexadecimal(binary_str: str) -> str:
    """
    Convert a binary string to a hexadecimal string.

    :param binary_str: A string representing a binary number (e.g., '1011').
    :return: The hexadecimal string equivalent of the binary string (e.g., 'B').
    """
    decimal_value = int(binary_str, base=2)
    return hex(decimal_value)[2:].upper()

def hexadecimal_to_binary(hex_str: str) -> str:
    """
    Convert a hexadecimal string to a binary string.

    :param hex_str: A string representing a hexadecimal number (e.g., 'B').
    :return: The binary string equivalent of the hexadecimal string (e.g., '1011').
    """
    decimal_value = int(hex_str, base=16)
    return bin(decimal_value)[2:]