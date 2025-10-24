from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from tqdm import tqdm

from edc_sites.site import sites

from .exceptions import HolidayFileNotFoundError, HolidayImportError
from .utils import get_holiday_model_cls

if TYPE_CHECKING:
    from .models import Holiday

LOCAL_DATE = 0
LABEL = 1
COUNTRY = 2


def import_holidays(verbose: bool | None = None, test: bool | None = None) -> None:
    model_cls = get_holiday_model_cls()
    if test:
        import_for_tests(model_cls)
    else:
        path = Path(settings.HOLIDAY_FILE)
        try:
            if not Path(path).exists():
                raise HolidayFileNotFoundError(path)
        except TypeError as e:
            raise HolidayImportError(
                f"Invalid path importing holiday file. See settings.HOLIDAY_FILE. Got {path}."
            ) from e
        if verbose:
            sys.stdout.write(
                f"\nImporting holidays from '{path}' into {model_cls._meta.label_lower}\n"
            )
        model_cls.objects.all().delete()

        recs = check_for_duplicates_in_file(path)

        import_file(path, recs, model_cls)

        if verbose:
            sys.stdout.write("Done.\n")


def check_for_duplicates_in_file(path: Path) -> list:
    """Returns a list of records."""
    with path.open("r") as f:
        reader = csv.DictReader(f, fieldnames=["local_date", "label", "country"])
        recs = [(row["local_date"], row["country"]) for row in reader]
    if len(recs) != len(list(set(recs))):
        raise HolidayImportError("Invalid file. Duplicate dates detected for a country")
    return recs


def import_file(path: Path, recs: list, model_cls: Holiday):
    with path.open("r") as f:
        reader = csv.DictReader(f, fieldnames=["local_date", "label", "country"])
        for index, row in tqdm(enumerate(reader), total=len(recs)):
            if index == 0:
                continue
            try:
                local_date = datetime.strptime(row["local_date"], "%Y-%m-%d").date()  # noqa: DTZ007
            except ValueError as e:
                raise HolidayImportError(
                    f"Invalid format when importing from {path}. Got '{e}'"
                ) from e
            else:
                try:
                    obj = model_cls.objects.get(country=row["country"], local_date=local_date)
                except ObjectDoesNotExist:
                    model_cls.objects.create(
                        country=row["country"], local_date=local_date, name=row["label"]
                    )
                else:
                    obj.name = row["label"]
                    obj.save()


def import_for_tests(model_cls: type[Holiday]):
    year = timezone.now().year
    country = sites.get_current_country()
    if not country:
        raise HolidayImportError(
            "Cannot determine default country when importing "
            "holidays for tests. Confirm SITE_ID is valid. See `import_for_tests`"
        )
    rows = [
        [f"{year}-01-02", "Public Holiday", country],
        [f"{year}-01-01", "New Year", country],
        [f"{year}-04-14", "Good Friday", country],
        [f"{year}-04-17", "Easter Monday", country],
        [f"{year}-05-01", "May Day/Labour Day", country],
        [f"{year}-05-25", "Ascension Day", country],
        [f"{year}-07-18", "Public Holiday", country],
        [f"{year}-09-30", "Botswana Day", country],
        [f"{year}-10-02", "Public Holiday", country],
        [f"{year}-12-25", "Christmas Day", country],
        [f"{year}-12-26", "Boxing Day", country],
    ]
    objs = []
    for index, row in tqdm(enumerate(rows), total=len(rows)):
        if index == 0:
            continue
        try:
            local_date = datetime.strptime(row[LOCAL_DATE], "%Y-%m-%d").date()  # noqa: DTZ007
        except ValueError as e:
            raise HolidayImportError(
                f"Invalid format when importing holidays (test). Got '{e}'"
            ) from e
        else:
            objs.append(
                model_cls(country=row[COUNTRY], local_date=local_date, name=row[LABEL])
            )
    with transaction.atomic():
        model_cls.objects.all().delete()
        model_cls.objects.bulk_create(objs)
