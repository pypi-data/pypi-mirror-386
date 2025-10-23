from dataclasses import dataclass
from typing import Tuple, Dict

# ------------------ Thevenin ------------------

@dataclass(frozen=True)
class Thevenin:
    Vth: float  # volts
    Rth: float  # ohms (>= 0)

    def for_load(self, RL: float) -> Dict[str, float]:
        """Return V_L, I_L, P_L for a load RL (ohms)."""
        if RL < 0:
            raise ValueError("RL must be >= 0")
        denom = self.Rth + RL
        V_L = 0.0 if RL == 0 else self.Vth * RL / denom
        I_L = self.Vth / denom if denom != 0 else float("inf")
        P_L = 0.0 if RL == 0 else (self.Vth**2) * RL / (denom**2)
        return {"V_L": V_L, "I_L": I_L, "P_L": P_L}

    def max_power(self) -> Tuple[float, float]:
        """Return (RL_opt, Pmax) for maximum power transfer."""
        if self.Rth < 0:
            raise ValueError("Rth must be >= 0")
        RL_opt = self.Rth
        Pmax = (self.Vth**2) / (4 * self.Rth) if self.Rth > 0 else 0.0
        return RL_opt, Pmax

    def to_norton(self) -> "Norton":
        """Convert to Norton: In = Vth/Rth (0 if Rth==0), Rn = Rth."""
        if self.Rth == 0:
            return Norton(In=float("inf"), Rn=0.0)  # ideal voltage source
        return Norton(In=self.Vth / self.Rth, Rn=self.Rth)


def thevenin_from_voc_isc(Voc: float, Isc: float) -> Thevenin:
    """Build Thevenin from open-circuit voltage and short-circuit current."""
    if Isc == 0:
        raise ValueError("Isc must be non-zero.")
    return Thevenin(Vth=float(Voc), Rth=float(Voc / Isc))


# ------------------ Norton ------------------

@dataclass(frozen=True)
class Norton:
    In: float   # amperes
    Rn: float   # ohms (>= 0)

    def for_load(self, RL: float) -> Dict[str, float]:
        """Return V_L, I_L, P_L for a load RL (ohms)."""
        if RL < 0:
            raise ValueError("RL must be >= 0")
        denom = self.Rn + RL
        # Current divider: I_L = In * (Rn / (Rn + RL))
        I_L = self.In * (self.Rn / denom) if denom != 0 else float("nan")
        V_L = I_L * RL
        P_L = V_L * I_L
        return {"V_L": V_L, "I_L": I_L, "P_L": P_L}

    def max_power(self) -> Tuple[float, float]:
        """Return (RL_opt, Pmax)."""
        if self.Rn < 0:
            raise ValueError("Rn must be >= 0")
        RL_opt = self.Rn
        Pmax = (self.In**2) * self.Rn / 4 if self.Rn > 0 else 0.0
        return RL_opt, Pmax

    def to_thevenin(self) -> Thevenin:
        """Convert to Thevenin: Vth = In*Rn, Rth = Rn."""
        return Thevenin(Vth=self.In * self.Rn, Rth=self.Rn)


def norton_from_voc_isc(Voc: float, Isc: float) -> Norton:
    """Build Norton from open-circuit voltage and short-circuit current."""
    if Isc == 0:
        raise ValueError("Isc must be non-zero.")
    R = float(Voc / Isc)
    return Norton(In=float(Isc), Rn=R)