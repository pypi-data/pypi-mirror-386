def power_vi(voltage, current) -> float:
    """
    Calculates power

    Arguments: voltage (float), current (float)
    Returns: power (W) -> float
    """
    return voltage * current

def power_ri(resistance, current) -> float:
    """
    Calculates power

    Arguments: resistance (float), current (float)
    Returns: power (W) -> float
    """
    return resistance * current**2

def power_rv(resistance, voltage) -> float:
    """
    Calculates power

    Arguments: resistance (float), voltage (float)
    Returns: power (W) -> float
    """
    return (voltage**2) / resistance

def voltage_divider(V_in, R1, R2) -> float:
    """
    Calculates voltage over R1, in a voltage divider.

    Arguments: 
        * Voltage in (V_in) -> float
        * Resistor 1 (R1) -> float
        * Resistor 2 (R2) -> float

    Returns: voltage (V) -> float 
    """
    return (R1 / (R1 + R2)) * V_in

def current_divider(I_in, R1, R2) -> float:
    """
    Calculates current through R1, in a current divider.

    Arguments: 
        * Current in (I_in) -> float
        * Resistor 1 (R1) -> float
        * Resistor 2 (R2) -> float

    Returns: current (I) -> float 
    """
    return (R2 / (R1 + R2)) * I_in