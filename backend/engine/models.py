from dataclasses import dataclass

#            
CATEGORIES = {
    "heating": (3600, 2, 3, 2),
    "water":   (3600, 2, 3, 2),
    "power":   (3600, 2, 3, 2),
    "flood":   (1200, 2, 3, 2),
    "transit": (1200, 2, 3, 1),
    "danger":  (1200, 3, 5, 3),
    "other":   (3600, None, None, None),   
}
MAX_WINDOW = 3600
VULNERABLE = {"nursery", "kindergarten", "primary_school", "secondary_school", "school_other",
              "hospital", "clinic", "nursing_home"}


@dataclass(slots=True)
class Report:
    id: str
    device_id: str
    category: str
    kind: str        
    t: float         
    cell11: str      
    cell10: str      
    cell8: str       
    source: str      
    text: str | None = None
