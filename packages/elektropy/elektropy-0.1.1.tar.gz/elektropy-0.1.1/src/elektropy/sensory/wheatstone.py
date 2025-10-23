def wheatstone_voltage(R, R1, R2, R3, Vin) -> float:
    """
    
    Calculate the output voltage of a Wheatstone bridge.
    R: Resistance of the sensor (ohms)
    R1, R2, R3: Known resistances (ohms)
    Vin: Input voltage (volts)
    Returns Vout (volts)

    """
    # Calculate the voltage at the midpoints of the two voltage dividers
    V_A = Vin * R2 / (R1 + R2)
    V_B = Vin * R3 / (R + R3)
    # Output voltage is the difference between these two voltages
    Vout = V_A - V_B
    return Vout

def wheatstone_balance_voltage(R, R1, Vin) -> float:
    """
    Calculate the output voltage of a Wheatstone bridge with R2 = R3, in other words a balanced Wheatstone bridge.
    R: Resistance of the sensor (ohms)
    R1: Known resistance (ohms)
    Vin: Input voltage (volts)
    Returns R2 = R3 (ohms) for balance (Vout = 0)

    """

    Vout = ((R - R1) / (R + R1)) * (Vin / 2)
    return Vout

def wheatstone_resistance(Vout, R1, R2, R3, Vin) -> float:
    """
    Calculate the resistance of the sensor in a Wheatstone bridge given the output voltage.
    Vout: Output voltage (volts)
    R1, R2, R3: Known resistances (ohms)
    Vin: Input voltage (volts)
    Returns R: Resistance of the sensor (ohms)

    """
    R = R1 * ((R2 * Vout + R3 * (Vin + Vout)) / (R2 * (Vin - Vout) - R3 * Vout))
    return R

def wheatstone_balance_resistance(R1, Vin, dV) -> float:
    """
    Calculate the resistance of the sensor in a balanced Wheatstone bridge given the output voltage.
    R1: Known resistance (ohms)
    Vin: Input voltage (volts)
    dV: Output voltage (volts)
    Returns R: Resistance of the sensor (ohms)

    """

    R = R1 * (1 + (4 * dV) / (Vin - 2 * dV))
    return R
    