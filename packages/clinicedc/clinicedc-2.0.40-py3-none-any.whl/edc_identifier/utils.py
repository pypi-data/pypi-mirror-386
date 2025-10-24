import re
import secrets

from edc_protocol.research_protocol_config import ResearchProtocolConfig

from .exceptions import SubjectIdentifierError


def is_subject_identifier_or_raise(subject_identifier, reference_obj=None, raise_on_none=None):
    """Returns the given subject identifier.

    * If the format of the `subject_identifier` is invalid,
      raises an exception.
    * If `subject_identifier` is None, does nothing, unless
      `raise_on_none` is `True`.
    """
    valid_subject_identifier = subject_identifier and re.match(
        ResearchProtocolConfig().subject_identifier_pattern, subject_identifier or ""
    )
    if not valid_subject_identifier or (not subject_identifier and raise_on_none):
        reference_msg = ""
        if reference_obj:
            reference_msg = f"See {reference_obj!r}. "
        raise SubjectIdentifierError(
            f"Invalid format for subject identifier. {reference_msg}"
            f"Got `{subject_identifier or ''}`. "
            f"Expected pattern `{ResearchProtocolConfig().subject_identifier_pattern}`"
        )
    return subject_identifier


def get_human_phrase(no_hyphen: bool | None = None) -> str:
    """Returns 6 digits split by a '-', e.g. DEC-96E.

    There are 213,127,200 permutations from an unambiguous alphabet.
    """

    alphabet = "ABCDEFGHKMNPRTUVWXYZ2346789"
    phrase = "".join(secrets.choice(alphabet) for i in range(6)).upper()
    if no_hyphen:
        return phrase
    return phrase[0:3] + "-" + phrase[3:6]


def convert_to_human_readable(identifier: str) -> str:
    if not identifier:
        return ""
    return "-".join(re.findall(r".{1,4}", identifier))
