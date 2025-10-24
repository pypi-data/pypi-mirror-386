# Copyright (c) 2025 Cumulocity GmbH

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta
from typing import Generator, List, ClassVar

from c8y_api._base_api import CumulocityRestApi
from c8y_api.model.matcher import JsonMatcher
from c8y_api.model._base import CumulocityResource, ComplexObject, harmonize_page_size
from c8y_api.model._parser import ComplexObjectParser, SimpleObjectParser, as_values as parse_as_values
from c8y_api.model._util import _DateUtil


@dataclasses.dataclass
class Change:
    """Change details fragment within an audit log."""
    attribute: str = None
    new_value: str = None
    previous_value: str = None
    type: str = None


class AuditRecord(ComplexObject):
    """Represents an Audit Record object within Cumulocity.

    Instances of this class are returned by functions of the corresponding
    Audits API. Use this class to create new or update AuditRecord objects.

    See also:  https://cumulocity.com/api/core/#tag/Audits
    """

    class Severity:
        """Audit severity levels."""
        MAJOR = 'MAJOR'
        CRITICAL = 'CRITICAL'
        MINOR = 'MINOR'
        WARNING = 'WARNING'
        INFORMATION = 'information'  # for whatever reason, this is used.

    class Type:
        """Audit record source types."""
        ALARM = "Alarm"
        APPLICATION = "Application"
        BULKOPERATION = "BulkOperation"
        CEPMODULE = "CepModule"
        CONNECTOR = "Connector"
        EVENT = "Event"
        GROUP = "Group"
        INVENTORY = "Inventory"
        INVENTORYROLE = "InventoryRole"
        OPERATION = "Operation"
        OPTION = "Option"
        REPORT = "Report"
        SINGLESIGNON = "SingleSignOn"
        SMARTRULE = "SmartRule"
        SYSTEM = "SYSTEM"
        TENANT = "Tenant"
        TENANT_AUTH_CONFIG = "TenantAuthConfig"
        TRUSTED_CERTIFICATES = "TrustedCertificates"
        USER = "User"
        USER_AUTHENTICATION = "UserAuthentication"

    _parser = ComplexObjectParser({
            'type': 'type',
            'time': 'time',
            'creation_time': 'creationTime',
            'activity': 'activity',
            'text': 'text',
            'severity': 'severity',
            'user': 'user',
            'application': 'application'}, ['changes'])

    _change_parser: ClassVar[SimpleObjectParser] = SimpleObjectParser({
            'attribute': 'attribute',
            'type': 'type',
            'previous_value': 'previousValue',
            'new_value': 'newValue'})

    _resource = '/audit/auditRecords'

    _accept = CumulocityRestApi.CONTENT_AUDIT_RECORD

    def __init__(self,
                 c8y: CumulocityRestApi = None,
                 type: str = None,   # noqa
                 time: str | datetime = None,
                 source: str = None,
                 activity: str = None,
                 text: str = None,
                 changes: List[Change] = None,
                 severity: str = None,
                 application: str = None,
                 user: str = None,
                 **kwargs):
        """Create a new AuditRecord object.

        Args:
            c8y (CumulocityRestApi):  Cumulocity connection reference; needs
                to be set for direct manipulation (create, delete)
            type (str):  Audit records type
            time (str|datetime):  Date/time of the audit records Can be
                provided as timezone-aware datetime object or formatted
                string (in standard ISO format incl. timezone:
                YYYY-MM-DD'T'HH:MM:SS.SSSZ as it is returned by the
                Cumulocity REST API).
                Use 'now' to set  to current datetime in UTC.
            source (str):  The object ID to which the audit is associated
            activity (str):  Summary of the action that was carried out
            text (str):  Details of the action that was carried out
            severity (str):  Severity of the audit record.
            application (str):  The application from which the record was created.
            user (str):  The user who carried out the activity
            kwargs:  Additional arguments are treated as custom fragments
        """
        super().__init__(c8y, **kwargs)
        self.type = type
        self.time = _DateUtil.ensure_timestring(time)
        self.creation_time = None  # undocumented property
        self.source = source
        self.activity = activity
        self.text = text
        self.changes: List[Change] = changes
        self.severity = severity   # undocumented property
        self.application = application
        self.user = user

    @property
    def datetime(self) -> datetime:
        """Convert the audit record's time to a Python datetime object.

        Returns:
            Standard Python datetime object
        """
        return super()._to_datetime(self.time)

    @property
    def creation_datetime(self) -> datetime:
        """Convert the audit record's creation time to a Python
        datetime object.

        Returns:
            Standard Python datetime object
        """
        return super()._to_datetime(self.creation_time)

    @classmethod
    def from_json(cls, json: dict) -> AuditRecord:
        # (no doc update required)
        obj = super()._from_json(json, AuditRecord())
        if 'source' in obj:
            obj.source = json['source']['id']
            if 'changes' in json:
                obj.changes = [cls._change_parser.from_json(x, Change()) for x in json['changes']]
        return obj

    def to_json(self, only_updated: bool = False) -> dict:
        # (no doc update required)
        obj_json = super()._to_json(only_updated, exclude={'creation_time'})
        # source and changes need to be set manually
        if self.source:
            obj_json['source'] = {'id': self.source}
        if self.changes is not None:
            obj_json['changes'] = [self._change_parser.to_json(x) for x in self.changes]
        return obj_json

    def create(self) -> AuditRecord:
        """Create the AuditRecord within the database.

        Returns:
            A fresh AuditRecord object representing what was
            created within the database (including the ID).
        """
        return super()._create()


class AuditRecords(CumulocityResource):
    """Provides access to the Audit API.

    This class can be used for get, search for, create, update and
    delete records within the Cumulocity database.

    See also:  https://cumulocity.com/api/core/#tag/Audits
    """

    def __init__(self, c8y):
        super().__init__(c8y, '/audit/auditRecords')

    def get(self, record_id: str) -> AuditRecord:
        """Retrieve a specific object from the database.

        Args:
            record_id (str):  The database ID of the audit record

        Returns:
            An AuditRecord instance representing the object in the database.
        """
        audit_obj = AuditRecord.from_json(self._get_object(record_id))
        audit_obj.c8y = self.c8y  # inject c8y connection into instance
        return audit_obj

    def select(
            self,
            expression: str = None,
            type: str = None, source: str = None, application: str = None, user: str = None,  # noqa (type)
            before: str | datetime = None, after: str | datetime = None,
            min_age: timedelta = None, max_age: timedelta = None,
            reverse: bool = False, limit: int = None,
            include: str | JsonMatcher = None, exclude: str | JsonMatcher = None,
            page_size: int = 1000, page_number: int = None,
            as_values: str | tuple | list[str | tuple] = None,
            **kwargs
    ) -> Generator[AuditRecord]:
        """Query the database for audit records and iterate over the results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters' specification.  Filters can be
        combined (within reason).

        Args:
            expression (str):  Arbitrary filter expression which will be
                passed to Cumulocity without change; all other filters
                are ignored if this is provided
            type (str):  Audit record type
            source (str):  Database ID of a source device
            application (str):  Application from which the audit was carried out.
            user (str): The user who carried out the activity.
            before (str|datetime):  Datetime object or ISO date/time string. Only
                records assigned to a time before this date are returned.
            after (str|datetime):  Datetime object or ISO date/time string. Only
                records assigned to a time after this date are returned.
            min_age (timedelta): Minimum age for selected records.
            max_age (timedelta): Maximum age for selected records.
            reverse (bool): Invert the order of results, starting with the
                most recent one.
            limit (int): Limit the number of results to this number.
            include (str | JsonMatcher): Matcher/expression to filter the query
                results (on client side). The inclusion is applied first.
                Creates a PyDF (Python Display Filter) matcher by default for strings.
            exclude (str | JsonMatcher): Matcher/expression to filter the query
                results (on client side). The exclusion is applied second.
                Creates a PyDF (Python Display Filter) matcher by default for strings.
            page_size (int): Define the number of objects which are read (and
                parsed in one chunk). This is a performance related setting.
            page_number (int): Pull a specific page; this effectively disables
                automatic follow-up page retrieval.
            as_values: (*str|tuple):  Don't parse objects, but directly extract
                the values at certain JSON paths as tuples; If the path is not
                defined in a result, None is used; Specify a tuple to define
                a proper default value for each path.

        Returns:
            Generator for AuditRecord objects

        See also:
            https://github.com/bytebutcher/pydfql/blob/main/docs/USER_GUIDE.md#4-query-language
        """
        base_query = self._prepare_query(
            expression=expression,
            type=type, source=source, application=application, user=user,
            before=before, after=after,
            min_age=min_age, max_age=max_age,
            reverse=reverse,
            page_size=harmonize_page_size(limit, page_size),
            **kwargs)
        return super()._iterate(
            base_query,
            page_number,
            limit,
            include,
            exclude,
            AuditRecord.from_json if not as_values else
            lambda x: parse_as_values(x, as_values))

    def get_all(
            self,
            expression: str = None,
            type: str = None, source: str = None, application: str = None, user: str = None,  # noqa (type)
            before: str | datetime = None, after: str | datetime = None,
            min_age: timedelta = None, max_age: timedelta = None,
            reverse: bool = False, limit: int = None,
            include: str | JsonMatcher = None, exclude: str | JsonMatcher = None,
            page_size: int = 1000, page_number: int = None,
            as_values: str | tuple | list[str | tuple] = None,
            **kwargs
    ) -> List[AuditRecord]:
        """Query the database for audit records and return the results as list.

        This function is a greedy version of the `select` function. All
        available results are read immediately and returned as list.

        See `select` for a documentation of arguments.

        Returns:
            List of AuditRecord objects
        """
        return list(self.select(
            expression=expression,
            type=type, source=source, application=application, user=user,
            before=before, after=after,
            min_age=min_age, max_age=max_age,
            reverse=reverse, limit=limit,
            include=include, exclude=exclude,
            page_size=page_size, page_number=page_number,
            as_values=as_values,
            **kwargs,
        ))

    def create(self, *records: AuditRecord):
        """Create audit record objects within the database.

        Note: If not yet defined, this will set the record date to now in
            each of the given objects.

        Args:
            *records (AuditRecord):  Collection of AuditRecord instances
        """
        for r in records:
            if not r.time:
                r.time = _DateUtil.to_timestring(datetime.utcnow())
        super()._create(AuditRecord.to_full_json, *records)
