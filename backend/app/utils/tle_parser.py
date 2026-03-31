import math

from app.models import StateVector

# WGS-84 Earth gravitational parameter (km^3/s^2)
MU_EARTH = 398600.4418
# Earth radius (km)
R_EARTH = 6378.137


def parse_tle(tle_line1: str, tle_line2: str) -> StateVector:
    """Convert a two-line element set into an approximate ECI state vector.

    This is a simplified Keplerian conversion (no perturbations).
    For high-fidelity work, use SGP4 via ``sgp4`` or ``poliastro``.
    """
    # --- Extract classical orbital elements from TLE line 2 ---
    inclination = math.radians(float(tle_line2[8:16].strip()))
    raan = math.radians(float(tle_line2[17:25].strip()))
    eccentricity = float(f"0.{tle_line2[26:33].strip()}")
    arg_perigee = math.radians(float(tle_line2[34:42].strip()))
    mean_anomaly_deg = float(tle_line2[43:51].strip())
    mean_motion = float(tle_line2[52:63].strip())  # rev/day

    # Semi-major axis from mean motion
    n = mean_motion * 2.0 * math.pi / 86400.0  # rad/s
    a = (MU_EARTH / (n * n)) ** (1.0 / 3.0)  # km

    # Mean anomaly → eccentric anomaly (Newton-Raphson)
    M = math.radians(mean_anomaly_deg)
    E = M
    for _ in range(20):
        E = E - (E - eccentricity * math.sin(E) - M) / (
            1.0 - eccentricity * math.cos(E)
        )

    # True anomaly
    nu = 2.0 * math.atan2(
        math.sqrt(1.0 + eccentricity) * math.sin(E / 2.0),
        math.sqrt(1.0 - eccentricity) * math.cos(E / 2.0),
    )

    # Perifocal coordinates
    r_mag = a * (1.0 - eccentricity * math.cos(E))
    p_pf = r_mag * math.cos(nu)
    q_pf = r_mag * math.sin(nu)

    vp_pf = -math.sqrt(MU_EARTH / (a * (1.0 - eccentricity**2))) * math.sin(nu)
    vq_pf = math.sqrt(MU_EARTH / (a * (1.0 - eccentricity**2))) * (
        eccentricity + math.cos(nu)
    )

    # Rotation matrix perifocal → ECI
    cos_O, sin_O = math.cos(raan), math.sin(raan)
    cos_w, sin_w = math.cos(arg_perigee), math.sin(arg_perigee)
    cos_i, sin_i = math.cos(inclination), math.sin(inclination)

    r11 = cos_O * cos_w - sin_O * sin_w * cos_i
    r12 = -(cos_O * sin_w + sin_O * cos_w * cos_i)
    r21 = sin_O * cos_w + cos_O * sin_w * cos_i
    r22 = -(sin_O * sin_w - cos_O * cos_w * cos_i)
    r31 = sin_w * sin_i
    r32 = cos_w * sin_i

    x = r11 * p_pf + r12 * q_pf
    y = r21 * p_pf + r22 * q_pf
    z = r31 * p_pf + r32 * q_pf

    vx = r11 * vp_pf + r12 * vq_pf
    vy = r21 * vp_pf + r22 * vq_pf
    vz = r31 * vp_pf + r32 * vq_pf

    return StateVector(x=x, y=y, z=z, vx=vx, vy=vy, vz=vz)
