import numpy as np

NIAMEY_COEFFS = [6.46864019e-03, -6.84291035e-01, -1.22030009e01]


def invert_quadratic(Q, poly, root="max"):
    """
    Invert a quadratic polynomial to get stage from discharge.

    Parameters:
    - Q: scalar or array of discharge values
    - poly: a degree-2 numpy.poly1d object
    - root: 'max' (default) or 'min' to choose which root to return

    Returns:
    - h: estimated stage(s)
    """
    Q = np.atleast_1d(Q)
    a, b, c = poly.coefficients  # poly1d stores in descending order

    h_values = []
    for q in Q:
        discriminant = b**2 - 4 * a * (c - q)
        if discriminant < 0:
            h_values.append(np.nan)
        else:
            sqrt_d = np.sqrt(discriminant)
            h1 = (-b + sqrt_d) / (2 * a)
            h2 = (-b - sqrt_d) / (2 * a)
            h_values.append(max(h1, h2) if root == "max" else min(h1, h2))

    return np.array(h_values) if len(h_values) > 1 else h_values[0]


def calculate_stage(Q, coeffs=None, root="max"):
    """
    Estimate stage from discharge using a quadratic polynomial.

    Parameters:
    - Q: scalar or array of discharge values
    - coeffs: coefficients of the polynomial (default is NIAMEY_COEFFS)
    - root: 'max' (default) or 'min' to choose which root to return

    Returns:
    - h: estimated stage(s)
    """
    if coeffs is None:
        coeffs = NIAMEY_COEFFS
    poly = np.poly1d(coeffs)
    return invert_quadratic(Q, poly, root=root)
