from django.conf import settings

ADVERSE_EVENT_APP_LABEL = getattr(settings, "ADVERSE_EVENT_APP_LABEL", "edc_adverse_event")
ADVERSE_EVENT_ADMIN_SITE = getattr(
    settings, "ADVERSE_EVENT_ADMIN_SITE", "edc_adverse_event_admin"
)
AESI_ACTION = "submit-aesi-report"
AE_FOLLOWUP_ACTION = "submit-ae-followup-report"
AE_INITIAL_ACTION = "submit-initial-ae-report"
AE_SUSAR_ACTION = "submit-ae-susar-report"
AE_TMG_ACTION = "submit-ae-tmg-report"
AE_WITHDRAWN = "ae_withdrawn"
CONTINUING_UPDATE = "continuing/update"
DEATH_REPORT_ACTION = "submit-death-report"
DEATH_REPORT_NOT_FOUND = "DEATH_REPORT_NOT_FOUND"
DEATH_REPORT_TMG_ACTION = "submit-death-report-tmg"
DEATH_REPORT_TMG_SECOND_ACTION = "submit-death-report-tmg-2nd"
DEFINITELY_RELATED = "definitely_related"
DISCHARGED = "discharged"
HOSPITALIZATION_ACTION = "submit-hospitalization-report"
INPATIENT = "inpatient"
NOT_RECOVERED = "not_recovered"
NOT_RELATED = "not_related"
POSSIBLY_RELATED = "possibly_related"
PROBABLY_RELATED = "probably_related"
RECOVERED = "recovered"
RECOVERED_WITH_SEQUELAE = "recovered_with_sequelae"
RECOVERING = "recovering"
STUDY_TERMINATION_CONCLUSION_ACTION = "submit-study-termination-conclusion"
UNLIKELY_RELATED = "unlikely_related"

# roles
AE = "AE"
AE_REVIEW = "AE_REVIEW"
AE_ROLE = "ae_role"
AE_SUPER = "AE_SUPER"
TMG = "TMG"
TMG_REVIEW = "TMG_REVIEW"
TMG_ROLE = "tmg"
