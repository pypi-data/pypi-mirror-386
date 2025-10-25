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
from functools import total_ordering
from typing import Annotated, Optional

from pydantic import BeforeValidator

from ..common_models import IdNameType, RFBaseModel
from ..constants import TIMESTAMP_STR
from ..helpers import Validators
from .models import (
    RequestDetection,
    RequestIOC,
    RequestOptions,
    SubmissionResult,
)


@total_ordering
class Insight(RFBaseModel):
    """Validate a single insight.

    This class supports hashing, equality comparison, string representation, and total
    ordering of `Insight` instances.

    Hashing:
        Returns a hash value based on the IOC value.

    Equality:
        Checks equality between two `Insight` instances based on their IOC value and timestamp.

    Greater-than Comparison:
        Defines a greater-than comparison between two `Insight` instances based on their
        timestamp and IOC value.

    String Representation:
        Returns a string representation of the `Insight` instance including the IOC value,
        timestamp, and detection type.

        ```python
        >>> print(insight)
        IOC: mal_dom.com, Timestamp: 2024-05-21 10:42:30AM, Detection Type: sandbox
        ```

    Total ordering:
        Ordering of `Insight` instances is determined primarily by the timestamp.
        If two instances have the same timestamp, their IOC value is used as a secondary criterion.
    """

    timestamp: datetime
    ioc: RequestIOC
    incident: Optional[IdNameType] = None
    mitre_codes: Annotated[Optional[list[str]], BeforeValidator(Validators.convert_str_to_list)] = (
        None
    )
    malwares: Annotated[Optional[list[str]], BeforeValidator(Validators.convert_str_to_list)] = None
    detection: RequestDetection

    def __hash__(self):
        return hash(self.ioc.value)

    def __eq__(self, other: 'Insight'):
        return (self.ioc.value, self.timestamp) == (other.ioc.value, other.timestamp)

    def __gt__(self, other: 'Insight'):
        return (self.timestamp, self.ioc.value) > (other.timestamp, other.ioc.value)

    def __str__(self):
        return (
            f'IOC: {self.ioc.value}, Timestamp: {self.timestamp.strftime(TIMESTAMP_STR)}, '
            f'Detection Type: {self.detection.type_}'
        )


class InsightsOut(RFBaseModel):
    """Validate data sent to CI."""

    options: Optional[RequestOptions] = None
    organization_ids: Optional[list[str]] = None
    data: list[Insight]


class InsightsIn(RFBaseModel):
    """Validate data received from CI."""

    result: SubmissionResult
