# my_math/geometry.py
import math

def calculate_circle_area(radius):
    """
    Calculates the area of a circle given its radius.
    """
    if radius < 0:
        raise ValueError("Radius cannot be negative.")
    return math.pi * radius**2