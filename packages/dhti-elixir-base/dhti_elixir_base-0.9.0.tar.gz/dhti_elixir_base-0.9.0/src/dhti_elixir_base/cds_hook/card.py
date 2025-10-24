"""Pydantic Model for CDS Hook Card

Example:

{
  "summary": "Patient is at high risk for opioid overdose.",
  "detail": "According to CDC guidelines, the patient's opioid dosage should be tapered to less than 50 MME. [Link to CDC Guideline](https://www.cdc.gov/drugoverdose/prescribing/guidelines.html)",
  "indicator": "warning",
  "source": {
    "label": "CDC Opioid Prescribing Guidelines",
    "url": "https://www.cdc.gov/drugoverdose/prescribing/guidelines.html",
    "icon": "https://example.org/img/cdc-icon.png"
  },
  "links": [
    {
      "label": "View MME Conversion Table",
      "url": "https://www.cdc.gov/drugoverdose/prescribing/mme.html"
    }
  ]
}

"""

from typing import List, Optional, Literal
from pydantic import BaseModel

class CDSHookCardSource(BaseModel):
    """Source of the CDS Hook Card"""
    label: str
    url: Optional[str] = None
    icon: Optional[str] = None

class CDSHookCardLink(BaseModel):
    """Link associated with the CDS Hook Card"""
    label: str
    url: str

class CDSHookCard(BaseModel):
    """CDS Hook Card Model"""
    summary: str
    detail: Optional[str] = None
    indicator: Optional[Literal["info", "warning", "hard-stop"]] = None
    source: Optional[CDSHookCardSource] = None
    links: Optional[List[CDSHookCardLink]] = None
