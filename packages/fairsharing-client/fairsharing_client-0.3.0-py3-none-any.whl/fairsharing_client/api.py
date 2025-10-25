"""Access to FAIRsharing via its API.

.. seealso:: https://beta.fairsharing.org/API_doc
"""

import json
from collections import defaultdict
from collections.abc import Iterable, MutableMapping
from pathlib import Path
from typing import Any, cast

import pystow
import requests
from tqdm import tqdm

__all__ = [
    "FairsharingClient",
    "ensure_fairsharing",
    "get_fairsharing_to_orcids",
    "load_fairsharing",
]

PATH = pystow.join("bio", "fairsharing", name="fairsharing.json")


def load_fairsharing(force_download: bool = False, use_tqdm: bool = True, **kwargs: Any) -> Any:
    """Get the FAIRsharing registry."""
    path = ensure_fairsharing(force_download=force_download, use_tqdm=use_tqdm, **kwargs)
    return json.loads(path.read_text())


def ensure_fairsharing(force_download: bool = False, use_tqdm: bool = True, **kwargs: Any) -> Path:
    """Get the FAIRsharing registry."""
    if PATH.exists() and not force_download:
        return PATH

    client = FairsharingClient(**kwargs)
    # As of 2021-12-13, there are a bit less than 4k records that take about 3 minutes to download
    rv = {
        row.pop("fairsharing_id"): row
        for row in tqdm(
            client.iter_records(),
            unit_scale=True,
            unit="record",
            desc="Downloading FAIRsharing",
            disable=not use_tqdm,
        )
    }

    PATH.write_text(json.dumps(rv, ensure_ascii=False, indent=2, sort_keys=True))
    return PATH


# These fields are the same in each record
REDUNDANT_FIELDS = {
    "fairsharing_licence",
    "type",
}


class FairsharingClient:
    """A client for programmatic access to the FAIRsharing private API."""

    def __init__(
        self,
        login: str | None = None,
        password: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Instantiate the client and get an appropriate JWT token.

        :param login: FAIRsharing username
        :param password: Corresponding FAIRsharing password
        :param base_url: The base URL
        """
        self.base_url = base_url or "https://api.fairsharing.org"
        self.signin_url = f"{self.base_url}/users/sign_in"
        self.records_url = f"{self.base_url}/fairsharing_records"
        self.username = pystow.get_config(
            "fairsharing", "login", passthrough=login, raise_on_missing=True
        )
        self.password = pystow.get_config(
            "fairsharing", "password", passthrough=password, raise_on_missing=True
        )
        self.jwt = self.get_jwt()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt}",
            }
        )

    def get_jwt(self) -> str:
        """Get the JWT."""
        payload = {
            "user": {
                "login": self.username,
                "password": self.password,
            },
        }
        res = requests.post(self.signin_url, json=payload, timeout=10)
        res.raise_for_status()
        res_json = res.json()
        if jwt := res_json.get("jwt"):
            return cast(str, jwt)
        raise ValueError(
            f"could not get JWT, are your login details right? "
            f"Response from FAIRsharing:\n\n  {res_json}\n"
        )

    def iter_records(self) -> Iterable[MutableMapping[str, Any]]:
        """Iterate over all FAIRsharing records."""
        yield from self._iter_records_helper(self.records_url)

    def _preprocess_record(
        self, in_record: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any] | None:
        attributes = in_record.pop("attributes")
        record = {**in_record, **attributes}
        doi = record.get("doi")
        if doi is None:
            # Records without a DOI can't be resolved
            url = record["url"]
            if not url.startswith("https://fairsharing.org/fairsharing_records/"):
                tqdm.write(f"{record['id']} has no DOI: {record['url']}")
            return None
        elif doi.startswith("10.25504/"):
            record["fairsharing_id"] = _removeprefix(doi, "10.25504/")
        else:
            tqdm.write(f"DOI has unexpected prefix: {record['doi']}")

        record["description"] = _removeprefix(
            record.get("description"), "This FAIRsharing record describes: "
        )
        record["name"] = _removeprefix(record.get("name"), "FAIRsharing record for: ")
        for key in REDUNDANT_FIELDS:
            record.pop(key, None)
        return record

    def _iter_records_helper(self, url: str) -> Iterable[MutableMapping[str, Any]]:
        res = self.session.get(url)
        res.raise_for_status()
        res_json = res.json()
        if "data" not in res_json or "links" not in res_json:
            raise ValueError(
                f"no data returned, are your login details right? "
                f"Response from FAIRsharing:\n\n  {res_json}\n"
            )
        for record in res_json["data"]:
            yv = self._preprocess_record(record)
            if yv:
                yield yv
        next_url = res_json["links"].get("next")
        if next_url:
            yield from self._iter_records_helper(next_url)


def _removeprefix(s: str | None, prefix: str) -> str | None:
    if s is None:
        return None
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s


def get_fairsharing_to_orcids() -> dict[str, set[str]]:
    """Get links from FAIRsharing IDs to sets of ORCID ids for people working on/credited."""
    from orcid_downloader import ground_researcher_unambiguous

    rv = defaultdict(set)
    rr = load_fairsharing()
    for fairsharing_id, record in rr.items():
        for contact in (record.get("metadata") or {}).get("contacts", []):
            orcid = contact.get("contact_orcid")
            name = contact.get("contact_name")
            if orcid:
                rv[fairsharing_id].add(orcid)
            elif name and (orcid := ground_researcher_unambiguous(name)):
                rv[fairsharing_id].add(orcid)

    return dict(rv)


if __name__ == "__main__":
    ensure_fairsharing(force_download=True)
