import math

def wrap_two_pi(angle: float):
    """
    Wraps an angle to be between -pi and pi radians.
    """
    return ((angle + math.pi) % (2 * math.pi)) - math.pi


def get_turn_angle(from_angle: float, to_angle: float) -> float:
    """
    Calculate minimum turn angle from from_angle to to_angle. Left turn is positive.
    """
    from_angle = wrap_two_pi(from_angle)
    to_angle = wrap_two_pi(to_angle)
    diff = to_angle - from_angle
    if diff > math.pi:
        diff -= math.pi * 2
    elif diff < -math.pi:
        diff += math.pi * 2
    return diff
