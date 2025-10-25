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
from os import environ

###############################################################################
# API Version
###############################################################################
API_VERSION = 'v2'

###############################################################################
# API Base URLs
###############################################################################
BASE_URL = 'https://api.recordedfuture.com'
CONNECT_API_BASE_URL = BASE_URL + '/' + API_VERSION

BASE_URL = environ.get('RF_BASE_URL') if environ.get('RF_BASE_URL') else BASE_URL
CONNECT_API_BASE_URL = (
    environ.get('RF_BASE_URL') if environ.get('RF_BASE_URL') else CONNECT_API_BASE_URL
)

###############################################################################
# Classic Alerts Endpoints V3
###############################################################################
EP_CLASSIC_ALERTS_V3 = BASE_URL + '/v3'
EP_CLASSIC_ALERTS_RULES = CONNECT_API_BASE_URL + '/alert/rule'
EP_CLASSIC_ALERTS_UPDATE = CONNECT_API_BASE_URL + '/alert/update'
EP_CLASSIC_ALERTS_SEARCH = EP_CLASSIC_ALERTS_V3 + '/alerts/'
EP_CLASSIC_ALERTS_HITS = EP_CLASSIC_ALERTS_V3 + '/alerts/hits'
EP_CLASSIC_ALERTS_IMAGE = EP_CLASSIC_ALERTS_V3 + '/alerts/image'
EP_CLASSIC_ALERTS_ID = EP_CLASSIC_ALERTS_V3 + '/alerts/{}'

###############################################################################
# Fusion Endpoints
###############################################################################
EP_RISKLIST = f'{BASE_URL}/{API_VERSION}/' + '{}/risklist'
EP_FUSION_FILES = CONNECT_API_BASE_URL + '/fusion/files'

EP_FUSION_FILES_V3 = f'{BASE_URL}/fusion/v3/files/'
EP_FUSION_DIR_V3 = f'{BASE_URL}/fusion/v3/files/directory/'

###############################################################################
# Playbook Alert Endpoints
###############################################################################
EP_PLAYBOOK_ALERT = BASE_URL + '/playbook-alert'
EP_PLAYBOOK_ALERT_SEARCH = EP_PLAYBOOK_ALERT + '/search'
EP_PLAYBOOK_ALERT_COMMON = EP_PLAYBOOK_ALERT + '/common'
EP_PLAYBOOK_ALERT_CODE_REPO_LEAKAGE = EP_PLAYBOOK_ALERT + '/code_repo_leakage'
EP_PLAYBOOK_ALERT_CYBER_VULNERABILITY = EP_PLAYBOOK_ALERT + '/vulnerability'
EP_PLAYBOOK_ALERT_DOMAIN_ABUSE = EP_PLAYBOOK_ALERT + '/domain_abuse'
EP_PLAYBOOK_ALERT_GEOPOLITICS_FACILITY = EP_PLAYBOOK_ALERT + '/geopolitics_facility'
EP_PLAYBOOK_ALERT_IDENTITY_NOVEL_EXPOSURES = EP_PLAYBOOK_ALERT + '/identity_novel_exposures'
EP_PLAYBOOK_ALERT_THIRD_PARTY_RISK = EP_PLAYBOOK_ALERT + '/third_party_risk'
EP_PLAYBOOK_ALERT_MALWARE_REPORT = EP_PLAYBOOK_ALERT + '/malware_report'

###############################################################################
# Entity Match Endpoint
###############################################################################
EP_ENTITY_MATCH = BASE_URL + '/entity-match/match'
EP_ENTITY_LOOKUP = BASE_URL + '/entity-match/entity/{}'

###############################################################################
# List API Endpoints
###############################################################################
EP_LIST = BASE_URL + '/list'
EP_CREATE_LIST = EP_LIST + '/create'
EP_SEARCH_LIST = EP_LIST + '/search'

###############################################################################
# SOAR Endpoints
###############################################################################
EP_SOAR_ENRICHMENT = BASE_URL + '/soar/v3/enrichment'

###############################################################################
# Detection Rules API Endpoints
###############################################################################
EP_DETECTION_RULES = BASE_URL + '/detection-rule/search'

###############################################################################
# Collective Insights API Endpoints
###############################################################################
EP_COLLECTIVE_INSIGHTS = BASE_URL + '/collective-insights'
EP_COLLECTIVE_INSIGHTS_DETECTIONS = EP_COLLECTIVE_INSIGHTS + '/detections'

###############################################################################
# Analyst Notes API Endpoints
###############################################################################
EP_ANALYST_NOTE = BASE_URL + '/analyst-note/'
EP_ANALYST_NOTE_SEARCH = EP_ANALYST_NOTE + 'search'
EP_ANALYST_NOTE_LOOKUP = EP_ANALYST_NOTE + 'lookup/{}'
EP_ANALYST_NOTE_PREVIEW = EP_ANALYST_NOTE + 'preview'
EP_ANALYST_NOTE_PUBLISH = EP_ANALYST_NOTE + 'publish'
EP_ANALYST_NOTE_DELETE = EP_ANALYST_NOTE + 'delete/{}'
EP_ANALYST_NOTE_ATTACHMENT = EP_ANALYST_NOTE + 'attachment/{}'

###############################################################################
# Identity API Endpoints
###############################################################################
EP_IDENTITY = BASE_URL + '/identity/'
EP_IDENTITY_DETECTIONS = EP_IDENTITY + 'detections'
EP_IDENTITY_INCIDENT_REPORT = EP_IDENTITY + 'incident/report'
EP_IDENTITY_HOSTNAME_LOOKUP = EP_IDENTITY + 'hostname/lookup'
EP_IDENTITY_PASSWORD_LOOKUP = EP_IDENTITY + 'password/lookup'
EP_IDENTITY_IP_LOOKUP = EP_IDENTITY + 'ip/lookup'
EP_IDENTITY_CREDENTIALS_SEARCH = EP_IDENTITY + 'credentials/search'
EP_IDENTITY_CREDENTIALS_LOOKUP = EP_IDENTITY + 'credentials/lookup'
EP_IDENTITY_DUMP_SEARCH = EP_IDENTITY + 'metadata/dump/search'

###############################################################################
# Malware Intelligence API Endpoints
###############################################################################
EP_MALWARE_INTELLIGENCE = BASE_URL + '/malware-intelligence/v1/'
EP_MALWARE_INTEL_REPORTS = EP_MALWARE_INTELLIGENCE + 'reports'

###############################################################################
# Risk History API Endpoints
###############################################################################
EP_RISK_HISTORY_BASE = BASE_URL + '/risk'
EP_RISK_HISTORY = EP_RISK_HISTORY_BASE + '/history'
