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

from functools import total_ordering
from typing import Annotated, Optional, Union

from pydantic import Field
from typing_extensions import Doc

from ..common_models import IdNameTypeDescription, RFBaseModel
from ..constants import TIMESTAMP_STR
from .constants import NOTES_PER_PAGE, URL_TO_PORTAL
from .markdown import _markdown
from .models import Attributes, PreviewAttributesIn, PreviewAttributesOut, RequestAttachment


# AnalystNote also used by BaseEnrichedEntity
@total_ordering
class AnalystNote(RFBaseModel):
    """Validate data received from the `/search` and `/analystnote/{note}` endpoints.

    This class supports hashing, equality comparison, string representation, and total ordering
    of `AnalystNote` instances.

    Hashing:
        Returns a hash value based on the note `id_`.

    Equality:
        Checks equality between two `AnalystNote` instances based on the `id_` and published time.

    Greater-than Comparison:
        Defines a greater-than comparison between two `AnalystNote` instances based on the published
        time and the `id_`.

    String Representation:
        Returns a string representation of the `AnalystNote` instance including the `id_`, `title`,
        and published timestamp.

        ```python
        >>> print(analyst_note)
        Analyst Note ID: 12345, Title: Cyber Vuln, Published: 2024-05-21 10:42:30AM
        ```

    Ordering:
        The ordering of `AnalystNote` instances is determined primarily by the published timestamp.
        If two instances have the same published timestamp, the note `id_` is used as a secondary
        criterion.
    """

    external_id: Optional[str] = None
    source: IdNameTypeDescription
    attributes: Attributes
    id_: str = Field(alias='id')

    def __hash__(self):
        return hash((self.id_, self.attributes.published))

    def __eq__(self, other: 'AnalystNote'):
        return (self.id_, self.attributes.published) == (other.id_, other.attributes.published)

    def __gt__(self, other: 'AnalystNote'):
        return (self.attributes.published, self.id_) > (other.attributes.published, other.id_)

    def __str__(self):
        return (
            f'Analyst Note ID: {self.id_}, Title: {self.attributes.title}, '
            f'Published: {self.attributes.published.strftime(TIMESTAMP_STR)}'
        )

    @property
    def detection_rule_type(self) -> Optional[str]:
        """Returns the attachment type if present, else None. It checks for specific types like
        `sigma rule`, `yara rule`, and `snort rule` in the topics of the note.
        """
        topics_type = ('sigma rule', 'yara rule', 'snort rule')

        topics = (
            {topic.name.lower() for topic in self.attributes.topic if topic.name}
            if isinstance(self.attributes.topic, list)
            else [self.attributes.topic.name]
        )

        return next(
            (topic_type.split()[0] for topic_type in topics_type if topic_type in topics),
            None,
        )

    @property
    def portal_url(self) -> str:
        """Get the link to portal."""
        if self.id_.startswith('doc:'):
            return URL_TO_PORTAL.format(self.id_)
        return URL_TO_PORTAL.format(f'doc:{self.id_}')

    def markdown(
        self,
        extract_entities: Annotated[
            bool, Doc('Extract and include entities in the markdown.')
        ] = True,
        diamond_model: Annotated[bool, Doc('Include a diamond model visualization.')] = True,
        html_tags: Annotated[bool, Doc('Include HTML tags in the output.')] = False,
        defang_malicious_infrastructure: Annotated[
            bool, Doc('Defang URLs or other malicious indicators.')
        ] = False,
        character_limit: Annotated[
            Optional[int],
            Doc('Limit the output to a specified number of characters.'),
        ] = None,
    ) -> Annotated[str, Doc('The generated markdown string.')]:
        """Return the markdown representation of the note."""
        return _markdown(
            self,
            extract_entities=extract_entities,
            diamond_model=diamond_model,
            html_tags=html_tags,
            defang_malicious_infrastructure=defang_malicious_infrastructure,
            character_limit=character_limit,
        )


class AnalystNotePreviewIn(RFBaseModel):
    """Validate data sent to `/preview` endpoint."""

    attributes: PreviewAttributesIn
    source: Optional[str]
    tagged_text: bool = False
    serialization: str = 'full'


class AnalystNotePreviewOut(RFBaseModel):
    """Validate data received from `/preview` endpoint."""

    attributes: PreviewAttributesOut
    source: IdNameTypeDescription


class AnalystNotePublishIn(AnalystNotePreviewIn):
    """Validate data sent to `/publish` endpoint."""

    attributes: PreviewAttributesIn
    source: Optional[str] = None
    tagged_text: bool = False
    serialization: str = 'full'
    note_id: Optional[str] = None
    resolve_entities: bool = True
    attachment_content_details: Optional[RequestAttachment] = None


class AnalystNotePublishOut(RFBaseModel):
    """Validate data received from `/publish` endpoint."""

    note_id: str


class AnalystNoteSearchIn(RFBaseModel):
    """Validate data sent to `/search` endpoint."""

    published: Optional[str] = None
    entity: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None
    topic: Union[list[str], str, None] = []
    label: Optional[str] = None
    source: Optional[str] = None
    serialization: str = None
    tagged_text: bool = None
    limit: int = NOTES_PER_PAGE
    from_: Optional[str] = Field(alias='from', default=None)
