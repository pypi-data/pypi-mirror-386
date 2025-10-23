def pt100_resistance(temperature_celsius: float, R0: float = 100.0, A: float = 3.9083e-3, B: float = -5.775e-7) -> float:
    """
    Calculate the resistance of a PT100 sensor at a given temperature.
    temperature_celsius: Temperature in degrees Celsius
    A, B: Callendar-Van Dusen coefficients for PT100
    Returns resistance in ohms.

    Works well for temperatures between 0 and 850 degrees Celsius.
    """  

    R = (R0 * (1 + A * (temperature_celsius)) + (B * temperature_celsius**2))
    return R

def pt100_temperature(resistance_ohms: float, R0: float = 100.0, A: float = 3.9083e-3, B: float = -5.775e-7) -> float:
    """
    Calculate the temperature in Celsius from the resistance of a PT100 sensor.
    resistance_ohms: Resistance in ohms
    A, B: Callendar-Van Dusen coefficients for PT100
    Returns temperature in degrees Celsius.

    Works well for temperatures between 0 and 850 degrees Celsius.
    """  
    # Using quadratic formula to solve for temperature
    discriminant = A**2 - 4 * B * (1 - (resistance_ohms / R0))
    if discriminant < 0:
        raise ValueError("Resistance value out of range for PT100 sensor.")
    
    sqrt_discriminant = discriminant**0.5
    temp1 = (-A + sqrt_discriminant) / (2 * B)
    temp2 = (-A - sqrt_discriminant) / (2 * B)

    # Return the physically meaningful solution (usually the positive one)
    return {'Solution 1: ', temp1, 'Solution 2: ', temp2}