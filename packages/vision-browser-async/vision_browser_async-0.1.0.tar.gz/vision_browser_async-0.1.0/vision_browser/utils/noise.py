from random import uniform


def random_noise_pref() -> dict:
    """
    Generate Vision-compatible noise preference.

    :returns: {"noise": float with 8 decimals}
    """
    value = round(uniform(1.0, 2.0), 8)
    return {"noise": value}