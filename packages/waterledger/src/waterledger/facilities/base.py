"""The facility contract (design 0010, level 2): what every large water user type gives Site and Estimate, so neither changes when a type is added.

A type is a Facility subclass with a `kind`, registered with @register. It declares its designs and which of them are evaporative (the default rules'
input), its size in its own unit, how its estimate is obtained (`results`), its BMI component (`bmi_config`) and the hooks below. Everything after
`results` reads only the roles (WaterUse, Electricity) and these hooks, never a type's own fields; a hook a type doesn't override means "this type has
none". A new hook is added here with a "none" default, never as a branch on type downstream."""
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from waterledger.estimate import Estimate
    from waterledger.site import Site

REGISTRY: dict[str, type["Facility"]] = {}


def register(cls):
    """Register a facility type by its `kind` (the discriminator Site.facility reads)."""
    kind = cls.model_fields["kind"].default
    if kind in REGISTRY and REGISTRY[kind] is not cls:
        raise ValueError(f"a facility type is already registered as {kind!r}: {REGISTRY[kind].__name__}")
    REGISTRY[kind] = cls
    return cls


class Facility(BaseModel):
    """A proposed large water user. Subclasses set `kind`, their own inputs and the contract below."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: str

    DESIGNS: ClassVar[tuple[str, ...]] = ()          # every design the type has, in the order by_design lists them
    EVAPORATIVE: ClassVar[tuple[str, ...]] = ()      # designs whose wastewater is mostly cooling blowdown (the default source and wastewater rules)
    DESIGN_FIELD: ClassVar[str] = "design"           # the field holding the design (a data center's is `cooling`)

    @property
    def design_name(self) -> str:
        """The facility's design, whatever its field is called."""
        return getattr(self, self.DESIGN_FIELD)

    def with_design(self, design: str) -> "Facility":
        """The same facility with another design."""
        if design not in self.DESIGNS:
            raise ValueError(f"{type(self).__name__} has no design {design!r}; it has {list(self.DESIGNS)}")
        return self.model_copy(update={self.DESIGN_FIELD: design})

    @property
    def size(self) -> tuple[float, str]:
        """(value, unit) for display: (300, "MW of IT capacity"), (43.75, "GWh/yr of cells")."""
        raise NotImplementedError

    def results(self, site: "Site", weather: str = "region") -> "Estimate":
        """The estimate's roles at the site: water, electricity and grid water, with the site's choices resolved, the model version and the data date.
        Comparisons, equivalents, before and after, levels and power plant water are added by Site.estimate from these alone."""
        raise NotImplementedError

    def bmi_config(self, forcing=None, end_time=None, design_db=None) -> tuple[str, dict]:
        """(entry point, config) of the BMI component that runs this facility step by step (Site.to_bmi_config writes it)."""
        raise NotImplementedError

    # hooks, each "none" unless the type overrides it

    def backup_generator_mw(self) -> float | None:
        """Backup generators on site, MW, for before and after's fuel row; None: none known for this type."""
        return None

    def cooling_blowdown(self, est: "Estimate") -> float | None:
        """Cooling tower blowdown sent back on an average day, MGD on the middle estimate, for runoff loads' blowdown phosphorus; None: none."""
        return None
