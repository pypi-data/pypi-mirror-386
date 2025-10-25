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

import re
from collections import defaultdict
from functools import total_ordering
from itertools import chain
from typing import Annotated, Optional

from pydantic import Field, NonNegativeInt, PositiveInt, model_validator
from typing_extensions import Doc

from ..common_models import RFBaseModel
from ..constants import DEFAULT_LIMIT, TIMESTAMP_STR
from ..playbook_alerts.markdown.markdown import _markdown_playbook_alert
from .models import (
    CodeRepoPanelEvidence,
    CodeRepoPanelStatus,
    CyberVulnerabilityPanelEvidence,
    CyberVulnerabilityPanelStatus,
    DatetimeRange,
    DomainAbusePanelEvidenceDns,
    DomainAbusePanelEvidenceSummary,
    DomainAbusePanelEvidenceWhois,
    DomainAbusePanelStatus,
    GeopolPanelEvents,
    GeopolPanelEvidence,
    GeopolPanelOverview,
    GeopolPanelStatus,
    IdentityPanelEvidence,
    IdentityPanelStatus,
    MalwareReportPanelEvidence,
    MalwareReportPanelStatus,
    TPRAssessment,
    TPRPanelEvidence,
    TPRPanelStatus,
)
from .models.panel_log import (
    CodeRepoLeakageEvidenceChange,
    DomainAbuseDnsChange,
    DomainAbuseLogoTypeChange,
    DomainAbuseMaliciousDnsChange,
    DomainAbuseMaliciousUrlChange,
    DomainAbuseReregistrationRecordChange,
    DomainAbuseScreenshotMentions,
    DomainAbuseWhoisChange,
    PanelLogV2,
    ThirdPartyAssessmentChange,
    VulnerabilityLifecycleChange,
)
from .models.panel_status import PanelAction, PanelStatus
from .pa_category import PACategory


@total_ordering
class PBA_Generic(RFBaseModel):
    """Base model for Playbook Alerts. Removes the deprecated `panel_log`.

    This model is intended to be inherited and should not be used directly.

    Hashing:
        Returns a hash value based on `playbook_alert_id` and the updated timestamp
        from the status panel.

    Equality:
        Checks equality between two `PBA_Generic` instances based on `playbook_alert_id`
        and the updated timestamp from the status panel.

    Greater-than Comparison:
        Compares two `PBA_Generic` instances based on updated timestamp from the
        status panel, using `playbook_alert_id` as a secondary criterion.

    String Representation:
        Returns a string representation of the alert:

        ```python
        >>> print(playbook_alert)
        Playbook Alert ID: task:a1ccb1c8-5554-42af, Updated: 2024-05-21 10:42:30AM,
        Category: Third Party Risk, Lookup Status: New
        ```

    Ordering:
        Ordering of `PBA_Generic` instances is based on the updated timestamp of the
        status panel. If timestamps are equal, `playbook_alert_id` is used as a tiebreaker.
    """

    playbook_alert_id: str
    panel_log_v2: Optional[list[PanelLogV2]] = []
    panel_status: Optional[PanelStatus] = Field(default_factory=PanelStatus)

    category: str = 'unmapped_alert'

    @model_validator(mode='before')
    @classmethod
    def remove_panel_log(cls, data):
        """Remove `panel_log` since it is deprecated."""
        if 'panel_log' in data:
            del data['panel_log']
        return data

    def __hash__(self):
        return hash((self.playbook_alert_id, self.panel_status.updated))

    def __eq__(self, other: 'PBA_Generic'):
        return (self.playbook_alert_id, self.panel_status.updated) == (
            other.playbook_alert_id,
            other.panel_status.updated,
        )

    def __gt__(self, other: 'PBA_Generic'):
        return (self.panel_status.updated, self.playbook_alert_id) > (
            other.panel_status.updated,
            other.playbook_alert_id,
        )

    def __str__(self):
        return (
            f'Playbook Alert ID: {self.playbook_alert_id}, '
            f'Updated: {self.panel_status.updated.strftime(TIMESTAMP_STR)}, '
            f'Category: {self.panel_status.case_rule_label}, '
            f'Lookup Status: {self.panel_status.status}'
        )

    def markdown(
        self,
        html_tags: Annotated[bool, Doc('Include HTML tags in the markdown output.')] = False,
        character_limit: Annotated[
            Optional[int],
            Doc('Character limit for the markdown output.'),
        ] = None,
        defang_iocs: Annotated[bool, Doc('Defang IOCs in markdown output.')] = False,
        extra_context: Annotated[
            Optional[list],
            Doc(
                """
                List of context models used by supported PBA classes when rendering markdown.
                Supported formats:
                - `PBA_ThirdPartyRisk`:
                    - `psengine.enrich.lookup.EnrichmentData`: enriched indicators or company
                    (risk field)
                    - `psengine.enrich.soar.SoarEnrichOut`: enriched indicators or company
                    - `psengine.analyst_notes.note.AnalystNotes`: analyst notes
                - `PBA_CyberVulnerability`:
                    - `psengine.enrich.lookup.EnrichmentData`: enriched CVE data (CVSSv2, CVSSv3,
                                                                                  or AI Insight)
                    """
            ),
        ] = None,
    ) -> Annotated[
        str,
        Doc('Markdown-formatted string representation of the Playbook Alert.'),
    ]:
        """Generate markdown for Playbook Alerts."""
        return _markdown_playbook_alert(
            self,
            html_tags=html_tags,
            character_limit=character_limit,
            defang_iocs=defang_iocs,
            extra_context=extra_context,
        )

    def _get_changes(self, change_type):
        """Filter for a specific change type from the v2 panel log."""
        changes = [obj.changes for obj in self.panel_log_v2]
        changes = [x for y in changes for x in y]
        return list(filter(lambda x: isinstance(x, change_type), changes))


class PBA_CodeRepoLeakage(PBA_Generic):
    """Model for Code Repo Leakage. Inherit behaviours from `PBA_Generic`."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    category: str = PACategory.CODE_REPO_LEAKAGE.value

    panel_status: Optional[CodeRepoPanelStatus] = Field(default_factory=CodeRepoPanelStatus)
    panel_evidence_summary: Optional[CodeRepoPanelEvidence] = Field(
        default_factory=CodeRepoPanelEvidence
    )

    @property
    def log_code_repo_leakage_evidence_changes(self) -> list:
        """Code Repo Leakage Evidence change."""
        return self._get_changes(CodeRepoLeakageEvidenceChange)


IPV4 = (
    r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.'
    r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)'
)
SEQ_IPV4 = r'((?:' + IPV4 + r'(?:,\s*)?)+)'


class PBA_ThirdPartyRisk(PBA_Generic):
    """Model for Third Party Risk. Inherit behaviours from `PBA_Generic`."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    category: str = PACategory.THIRD_PARTY_RISK.value

    panel_status: Optional[TPRPanelStatus] = Field(default_factory=TPRPanelStatus)
    panel_evidence_summary: Optional[TPRPanelEvidence] = Field(default_factory=TPRPanelEvidence)

    @property
    def log_third_party_assessment_changes(self) -> list:
        """Third Party Assessment change."""
        return self._get_changes(ThirdPartyAssessmentChange)

    def ips_from_ip_rule(
        self,
        assessment: Annotated[
            TPRAssessment, Doc('An assessment object to extract IPs and risk rules from.')
        ],
    ) -> Annotated[
        tuple[str, dict[str, list[str]]],
        Doc('Tuple containing a risk label and a dict of IP rule names mapped to IP addresses.'),
    ]:
        """Extracts via regex the IP addresses of each IP Rule in `assessment.nevidence.summary`.

        The addresses are deduplicated and sorted.

        Example:
            Return value example:
            ```python
            ('IT Policy Violations', {'Recent Tor Node': ['47.91.72.129', '47.254.128.11'}])
            ```
        """
        if assessment.evidence.type_ != 'ip_rule':
            return '', {}

        names = [entry.name for entry in assessment.evidence.data]
        risk_rule = assessment.risk_rule
        result = {}

        for name in names:
            pattern = (
                re.escape(name)
                + r' seen for \d+ IP Address(?:es)? on company infrastructure(?::)?(?: including)? '
                + SEQ_IPV4
            )
            matches = re.search(pattern, assessment.evidence.summary)
            if matches:
                result[name] = sorted(
                    {client_ip.strip() for client_ip in matches.group(1).split(',') if client_ip}
                )

        return risk_rule, result

    @property
    def ip_address_by_assessment(
        self,
    ) -> Annotated[
        dict[list],
        Doc('Key is an assessment type and value is a deduplicated, sorted list of IP addresses.'),
    ]:
        """Get all IP addresses that this PBA has, divided by assessment type.

        This function searches for indicators inside the assessments of type:

            - `ip_rule`
            - `hosts_communication` (malware IPs)
        """
        data = defaultdict(set)
        if not self.panel_evidence_summary.assessments:
            return {}

        for assessment in self.panel_evidence_summary.assessments:
            if assessment.evidence.type_ == 'ip_rule':
                _, ips_from_summary = self.ips_from_ip_rule(assessment)
                data['ip_rule'] = data['ip_rule'].union(
                    chain.from_iterable(ips_from_summary.values())
                )

            if assessment.evidence.type_ == 'hosts_communication':
                assess_data = assessment.evidence.data or []
                malware_ips = {
                    row.malware_ip_address for row in assess_data if row.malware_ip_address
                }
                data['hosts_communication'] = data['hosts_communication'].union(malware_ips)

        return {k: sorted(v) for k, v in data.items()}

    @property
    def all_ip_addresses(self) -> list:
        """Return a sorted list of all the IP addresses of the alert."""
        return sorted(chain.from_iterable(self.ip_address_by_assessment.values()))

    @property
    def all_insikt_notes(self) -> list:
        """Return a list of all the analyst notes IDs for the alert."""
        return list(
            {
                note.id_
                for a in self.panel_evidence_summary.assessments
                for note in a.evidence.data
                if a.evidence.type_ == 'insikt_note'
            }
        )


class PBA_CyberVulnerability(PBA_Generic):
    """Model for Cyber Vulnerability. Inherit behaviours from `PBA_Generic`."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    category: str = PACategory.CYBER_VULNERABILITY.value

    panel_status: Optional[CyberVulnerabilityPanelStatus] = Field(
        default_factory=CyberVulnerabilityPanelStatus
    )
    panel_evidence_summary: Optional[CyberVulnerabilityPanelEvidence] = Field(
        default_factory=CyberVulnerabilityPanelEvidence
    )

    @property
    def lifecycle_stage(self) -> str:
        """Get playbook alert `lifecycle_stage`."""
        if stage := self.panel_status.lifecycle_stage:
            return stage
        return self.panel_evidence_summary.summary.lifecycle_stage

    @property
    def log_vulnerability_lifecycle_changes(self) -> list:
        """Get `VulnerabilityLifecycleChange` log changes."""
        return self._get_changes(VulnerabilityLifecycleChange)

    @property
    def insikt_note_ids(self) -> list[str]:
        """Get Insikt note IDs if found in `self.panel_evidence_summary.insikt_notes`."""
        if self.panel_evidence_summary.insikt_notes:
            return [insikt_note.id_ for insikt_note in self.panel_evidence_summary.insikt_notes]
        return []


class PBA_IdentityNovelExposure(PBA_Generic):
    """Model for Identity Exposure. Inherit behaviours from `PBA_Generic`."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    category: str = PACategory.IDENTITY_NOVEL_EXPOSURES.value

    panel_status: Optional[IdentityPanelStatus] = Field(default_factory=IdentityPanelStatus)
    panel_evidence_summary: Optional[IdentityPanelEvidence] = Field(
        default_factory=IdentityPanelEvidence
    )

    @property
    def assessment_names(self) -> list[str]:
        """Assessments contain name and criticality, this returns all assessment names."""
        if not (self.panel_evidence_summary and self.panel_evidence_summary.assessments):
            return []
        return [assessment.name for assessment in self.panel_evidence_summary.assessments]

    @property
    def technology_names(self) -> list[str]:
        """Return the technologies names list."""
        if not self.panel_evidence_summary or not self.panel_evidence_summary.technologies:
            return []
        return [tech.name for tech in self.panel_evidence_summary.technologies]


class PBA_DomainAbuse(PBA_Generic):
    """Model for Domain Abuse. Inherit behaviours from `PBA_Generic`."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    _images: Optional[dict] = {}

    category: str = PACategory.DOMAIN_ABUSE.value

    panel_action: Optional[list[PanelAction]] = []
    panel_status: Optional[DomainAbusePanelStatus] = Field(default_factory=DomainAbusePanelStatus)
    panel_evidence_summary: Optional[DomainAbusePanelEvidenceSummary] = Field(
        default_factory=DomainAbusePanelEvidenceSummary
    )
    panel_evidence_dns: Optional[DomainAbusePanelEvidenceDns] = Field(
        default_factory=DomainAbusePanelEvidenceDns
    )
    panel_evidence_whois: Optional[DomainAbusePanelEvidenceWhois] = Field(
        default_factory=DomainAbusePanelEvidenceWhois
    )

    def store_image(self, image_id: str, image_bytes: bytes) -> None:
        """Domain Abuse: store image bytes in `self._images` dictionary.

        Raises:
            ValueError: if the `image_id` is not present in alert screenshots list
        """
        image_id_matches = list(
            filter(
                lambda x: x.image_id == image_id,
                self.panel_evidence_summary.screenshots,
            )
        )
        if len(image_id_matches) == 0:
            raise ValueError(
                f"Alert '{self.playbook_alert_id}' does not contain image id: '{image_id}'"
            )
        image_info = image_id_matches[0]
        self._images[image_id] = {}
        self._images[image_id]['description'] = image_info.description
        self._images[image_id]['created'] = image_info.created
        self._images[image_id]['image_bytes'] = image_bytes

    @property
    def image_ids(self) -> list[str]:
        """Get the playbook alert image IDs."""
        ids = []
        if self.panel_evidence_summary.screenshots:
            ids = [screenshot.image_id for screenshot in self.panel_evidence_summary.screenshots]
        return ids

    @property
    def images(
        self,
    ) -> Annotated[
        dict,
        Doc('Dict containing alert images with metadata and raw bytes, or empty if not found.'),
    ]:
        """Domain Abuse: Get raw bytes of the screenshots.

        This data is stored in the following format:

        ```python
        {
            image_id : {
                'description': "awesome image description",
                'created': "date",
                'image_bytes': b'xyz'
            }
        }
        ```
        """
        return self._images

    @property
    def log_dns_changes(self) -> list:
        """DNS change."""
        return self._get_changes(DomainAbuseDnsChange)

    @property
    def log_whois_changes(self) -> list:
        """WHOIS change."""
        return self._get_changes(DomainAbuseWhoisChange)

    @property
    def log_logotype_changes(self) -> list:
        """Logotype change."""
        return self._get_changes(DomainAbuseLogoTypeChange)

    @property
    def log_malicious_dns_changes(self) -> list:
        """Malaicious DNS change."""
        return self._get_changes(DomainAbuseMaliciousDnsChange)

    @property
    def log_reregistration_changes(self) -> list:
        """Reregistration change."""
        return self._get_changes(DomainAbuseReregistrationRecordChange)

    @property
    def log_malicious_url_changes(self) -> list:
        """Malicious URL change."""
        return self._get_changes(DomainAbuseMaliciousUrlChange)

    @property
    def log_screenshot_mentions_changes(self) -> list:
        """Screenshot mentions change."""
        return self._get_changes(DomainAbuseScreenshotMentions)


class PBA_GeopoliticsFacility(PBA_Generic):
    """Model for Geopolitics Facility. Inherit behaviours from `PBA_Generic`."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    _images: Optional[dict] = {}
    category: str = PACategory.GEOPOLITICS_FACILITY.value

    panel_status: Optional[GeopolPanelStatus] = Field(default_factory=GeopolPanelStatus)
    panel_evidence_summary: Optional[GeopolPanelEvidence] = Field(
        default_factory=GeopolPanelEvidence
    )
    panel_overview: Optional[GeopolPanelOverview] = Field(default_factory=GeopolPanelOverview)
    panel_events_summary: Optional[GeopolPanelEvents] = Field(default_factory=GeopolPanelEvents)

    @property
    def image_ids(self) -> list[str]:
        """Get the playbook alert image IDs."""
        return list(
            chain.from_iterable(
                [
                    e.images
                    for e in self.panel_events_summary.events
                    if self.panel_events_summary.events
                ]
            )
        )

    @property
    def images(
        self,
    ) -> Annotated[
        dict,
        Doc('Dict containing alert images with metadata and raw bytes, or empty if not found.'),
    ]:
        """Geopolitics Facility: Get raw bytes of the screenshots.

        This data is stored in the following format:

        ```python
        {
            image_id : {
                'created': "date",
                'image_bytes': b'xyz'
            }
        }
        ```
        """
        return self._images

    def store_image(self, image_id: str, image_bytes: bytes) -> None:
        """Geopolitics Facility: store image bytes in `self._images` dictionary.

        Raises:
            ValueError: if the image_id is not present in alert screenshots list
        """
        events_with_images = [e for e in self.panel_events_summary.events if e.images]

        if not (events_with_images and any(image_id in e.images for e in events_with_images)):
            raise ValueError(
                f"Alert '{self.playbook_alert_id}' does not contain image id: '{image_id}'"
            )
        for event in events_with_images:
            if image_id in event.images:
                matched_event = event
                break

        self._images[image_id] = {}
        self._images[image_id]['created'] = matched_event.time
        self._images[image_id]['image_bytes'] = image_bytes


class PBA_MalwareReport(PBA_Generic):
    """Model for Malware Report. Inherit behaviours from `PBA_Generic`."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    _images: Optional[dict] = {}

    category: str = PACategory.MALWARE_REPORT.value

    panel_status: Optional[MalwareReportPanelStatus] = Field(
        default_factory=MalwareReportPanelStatus
    )
    panel_evidence_summary: Optional[MalwareReportPanelEvidence] = Field(
        default_factory=MalwareReportPanelEvidence
    )


class SearchIn(RFBaseModel):
    """Model for payload sent to `/search` endpoint."""

    from_: Optional[NonNegativeInt] = Field(alias='from', default=None)
    limit: Optional[PositiveInt] = DEFAULT_LIMIT
    order_by: Optional[str] = None
    direction: Optional[str] = None
    entity: Optional[list] = None
    statuses: Optional[list[str]] = None
    priority: Optional[list[str]] = None
    category: Optional[list[str]] = None
    assignee: Optional[list[str]] = None
    created_range: Optional[DatetimeRange] = None
    updated_range: Optional[DatetimeRange] = None


class PreviewAlertOut(PanelStatus):
    """Model for payload received by GET `/common/{alert_id}` endpoint."""

    playbook_alert_id: str
    title: str
    category: str


class UpdateAlertIn(RFBaseModel):
    """Model for payload sent to PUT `/common/{playbook_alert_id}` endpoint."""

    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    log_entry: Optional[str] = None
    reopen: Optional[str] = None
    added_actions_taken: Optional[list[str]] = None
    removed_actions_taken: Optional[list[str]] = None
