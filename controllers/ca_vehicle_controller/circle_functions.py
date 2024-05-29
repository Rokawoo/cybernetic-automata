import random
import numpy as np
import math

def generate_random_point_in_circle(radius):
    """
    Generate a random point within a circle of given radius.

    Args:
        radius (float): Radius of the circle.

    Returns:
        tuple: Coordinates (x, y) of the generated point.
    """
    theta = random.uniform(0, 2 * math.pi)
    r = random.uniform(0, radius)
    x = r * math.cos(theta)
    y = r * math.sin(theta)
    return x, y

def origin_distance_quadrant(x, y):
    """
    Calculate distance from origin and quadrant number for a point.

    Args:
        x (float): x-coordinate of the point.
        y (float): y-coordinate of the point.

    Returns:
        tuple: Distance from origin and quadrant number.
    """
    rho = np.sqrt(x ** 2 + y ** 2)
    phi = np.arctan2(y, x)
    phi = (phi + 2 * np.pi) % (2 * np.pi)
    quadrants = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}
    quadrant = 0
    for key, value in quadrants.items():
        if math.pi / 4 * (2 * key + 1) <= phi < math.pi / 4 * (2 * (key + 1) + 1):
            quadrant = value
            break
    return rho, quadrant

def rotate_list(lst, amount):
    """
    Rotate a list by a specified amount.

    Args:
        lst (list): The list to rotate.
        amount (int): The number of positions to rotate.

    Returns:
        list: The rotated list.
    """
    amount %= len(lst)
    return lst[amount:] + lst[:amount]

def rotate_tuple(tup, amount):
    """
    Rotate a tuple by a specified amount.

    Args:
        tup (tuple): The tuple to rotate.
        amount (int): The number of positions to rotate.

    Returns:
        tuple: The rotated tuple.
    """
    amount %= len(tup)
    return tup[amount:] + tup[:amount]

def calculate_min_steps(distance, rotation):
    """
    Calculate the minimum steps needed based on distance and rotation.

    Args:
        distance (float): Distance from the origin.
        rotation (int): Quadrant number.

    Returns:
        int: The calculated minimum steps.
    """
    min_steps = round(distance * 6.25) if distance >= 0.3 else 0
    if rotation == 0:
        min_steps += 4
    elif rotation in (1, 7):
        min_steps += 3
    elif rotation in (2, 6):
        min_steps += 2
    elif rotation in (3, 5):
        min_steps += 1
    return min_steps

if __name__ == "__main__":
    radius = 2.4
    x, y = generate_random_point_in_circle(radius)
    print("XY:", x, y)
    
    rho, quadrant = origin_distance_quadrant(x, y)
    print(f"The point ({x}, {y}) is in Quadrant {quadrant}.")
    print(f"The distance from the origin is {rho:.2f} units.")
    
    t_list = [0, 1, 2, 3, 4, 5, 6, 7]
    print(rotate_list(t_list, quadrant))
    
    print(calculate_min_steps(1, quadrant))
