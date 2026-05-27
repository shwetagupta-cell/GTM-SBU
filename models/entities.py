from dataclasses import dataclass, field
from typing import Dict, List, Union


@dataclass
class ProjectRecord:
    project_id: str
    project_name: str
    project_value: float = 0.0
    future_value: float = 0.0
    monthly_cf: Dict[str, float] = field(default_factory=dict)
    monthly_incentive: Dict[str, float] = field(default_factory=dict)
    closure_roles: List[str] = field(default_factory=list)
    sourcing_type: str = ""
    ytd_meta: Dict[str, Union[float, str]] = field(default_factory=dict)
    source_sheet: str = ""


@dataclass
class EmployeeRecord:
    employee_id: str
    name: str
    designation: str = ""
    location: str = ""
    email: str = ""
    team_head_id: str = ""
    team_head_name: str = ""
    month_order: List[str] = field(default_factory=list)
    managed_employee_ids: List[str] = field(default_factory=list)
    projects: List[ProjectRecord] = field(default_factory=list)
    must_change_password: bool = True

    @property
    def is_team_head(self) -> bool:
        return bool(self.managed_employee_ids)
