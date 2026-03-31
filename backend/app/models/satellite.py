from pydantic import BaseModel, Field

from .state_vector import StateVector


# Default exhaust velocity for typical satellite thrusters (hydrazine monoprop)
# Ve = Isp * g0, where Isp ~ 220s for hydrazine, g0 = 9.81 m/s^2
DEFAULT_EXHAUST_VELOCITY_MS = 2157.0  # m/s


class Satellite(BaseModel):
    """Satellite model with propulsion parameters for Tsiolkovsky calculations."""

    id: str
    name: str
    state: StateVector

    # Mass properties (kg)
    fuel_mass: float = Field(ge=0, description="Current fuel mass in kg")
    dry_mass: float = Field(gt=0, description="Dry mass (without fuel) in kg")
    initial_fuel_mass: float = Field(
        default=None, description="Initial fuel mass at mission start"
    )

    # Propulsion parameters
    exhaust_velocity_ms: float = Field(
        default=DEFAULT_EXHAUST_VELOCITY_MS,
        description="Effective exhaust velocity in m/s (Ve = Isp * g0)",
    )

    # Operational constraints
    min_fuel_reserve_kg: float = Field(
        default=1.0, description="Minimum fuel reserve for station-keeping"
    )
    max_delta_v_per_burn_ms: float = Field(
        default=15.0, description="Maximum delta-v per single burn in m/s"
    )

    # Status flags
    is_maneuverable: bool = Field(
        default=True, description="Whether satellite can perform maneuvers"
    )
    is_healthy: bool = Field(default=True, description="Overall health status")

    def __init__(self, **data):
        super().__init__(**data)
        # Set initial fuel mass if not provided
        if self.initial_fuel_mass is None:
            object.__setattr__(self, "initial_fuel_mass", self.fuel_mass)

    @property
    def total_mass(self) -> float:
        """Total current mass (dry + fuel) in kg."""
        return self.dry_mass + self.fuel_mass

    @property
    def available_fuel(self) -> float:
        """Fuel available for maneuvers (above reserve) in kg."""
        return max(0.0, self.fuel_mass - self.min_fuel_reserve_kg)

    @property
    def fuel_fraction_remaining(self) -> float:
        """Fraction of initial fuel remaining (0 to 1)."""
        if self.initial_fuel_mass and self.initial_fuel_mass > 0:
            return self.fuel_mass / self.initial_fuel_mass
        return 0.0

    def can_perform_burn(self, delta_v_ms: float) -> tuple[bool, str]:
        """Check if the satellite can perform a burn with the given delta-v.

        Returns:
            Tuple of (can_perform, reason_if_not)
        """
        if not self.is_maneuverable:
            return False, "Satellite is not maneuverable"

        if not self.is_healthy:
            return False, "Satellite is unhealthy"

        if delta_v_ms > self.max_delta_v_per_burn_ms:
            return False, f"Delta-v {delta_v_ms:.2f} m/s exceeds max {self.max_delta_v_per_burn_ms:.2f} m/s"

        # Calculate required fuel using Tsiolkovsky
        import math

        mass_ratio = math.exp(delta_v_ms / self.exhaust_velocity_ms)
        required_fuel = self.total_mass * (1 - 1 / mass_ratio)

        if required_fuel > self.available_fuel:
            return False, f"Insufficient fuel: need {required_fuel:.3f} kg, have {self.available_fuel:.3f} kg available"

        return True, "OK"

    def calculate_fuel_for_delta_v(self, delta_v_ms: float) -> float:
        """Calculate fuel required for a given delta-v using Tsiolkovsky equation.

        Args:
            delta_v_ms: Delta-v in m/s

        Returns:
            Required fuel mass in kg
        """
        import math

        # Tsiolkovsky: delta_v = Ve * ln(m0/m1)
        # m0 = initial mass, m1 = final mass
        # m0/m1 = exp(delta_v / Ve)
        # fuel = m0 - m1 = m0 * (1 - 1/exp(delta_v/Ve))

        mass_ratio = math.exp(delta_v_ms / self.exhaust_velocity_ms)
        fuel_consumed = self.total_mass * (1 - 1 / mass_ratio)
        return fuel_consumed

    def calculate_max_delta_v(self) -> float:
        """Calculate maximum delta-v possible with available fuel.

        Returns:
            Maximum delta-v in m/s
        """
        import math

        if self.available_fuel <= 0:
            return 0.0

        # m0 = current total mass
        # m1 = mass after using available fuel
        m0 = self.total_mass
        m1 = m0 - self.available_fuel

        if m1 <= 0:
            return float("inf")

        return self.exhaust_velocity_ms * math.log(m0 / m1)
