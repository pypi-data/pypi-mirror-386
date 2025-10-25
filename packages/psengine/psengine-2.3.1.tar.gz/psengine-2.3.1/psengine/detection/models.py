##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BeforeValidator, Field

from ..common_models import DetectionRuleType, RFBaseModel
from ..helpers import Validators


class Entity(RFBaseModel):
    id_: str = Field(alias='id', default=None)
    name: Optional[str] = None
    type_: str = Field(alias='type', default=None)

    display_name: Optional[str] = None


class RuleContext(RFBaseModel):
    entities: list[Entity]
    content: str
    file_name: Optional[str] = None


class TimeRange(RFBaseModel):
    after: Annotated[Optional[datetime], BeforeValidator(Validators.convert_relative_time)] = None
    before: Annotated[Optional[datetime], BeforeValidator(Validators.convert_relative_time)] = None


class SearchFilter(RFBaseModel):
    types: Annotated[
        Optional[list[DetectionRuleType]], BeforeValidator(Validators.convert_str_to_list)
    ] = None
    entities: Optional[list[str]] = None
    created: Optional[TimeRange] = None
    updated: Optional[TimeRange] = None
    doc_id: Optional[str] = None
    title: Optional[str] = None
