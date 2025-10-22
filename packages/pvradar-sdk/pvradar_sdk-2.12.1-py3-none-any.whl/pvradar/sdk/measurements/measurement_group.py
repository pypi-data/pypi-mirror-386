from abc import ABC, abstractmethod
from functools import cached_property
from typing import Any, Mapping, Optional, Self, override, TypedDict

import pandas as pd
from pvlib.location import Location

from ..client.api_query import Query
from ..client.client import PvradarClient
from ..client.pvradar_site import PvradarSite
from ..modeling.basics import ResourceRecord, Confidentiality
from ..modeling.utils import attrs_as_descriptor_mapping, is_attrs_convertible, convert_by_attrs
from ..pv.design import PvradarSiteDesign, make_fixed_design, make_tracker_design
from ..common.pandas_utils import is_series_or_frame
from ..common.exceptions import PvradarSdkError
from ..modeling import R


# fixed_design_spec_resource_type = 'fixed_design_spec'
# tracker_design_spec_resource_type = 'tracker_design_spec'
default_confidentiality: Confidentiality = 'internal'


class GroupMeta(TypedDict):
    min_timestamp: str | None
    max_timestamp: str | None
    utc_offset: int | None
    lat: float | None
    lon: float | None
    confidentiality: Confidentiality
    org_id: Optional[str]


class AbstractMeasurementGroup(PvradarSite, ABC):
    def __init__(
        self,
        id: str,
        *,
        location: Optional[Location | tuple | str] = None,
        interval: Optional[Any] = None,
        default_tz: Optional[str] = None,
        design: Optional[PvradarSiteDesign] = None,
        attrs: Optional[dict[str, Any]] = None,
        **kwargs,
    ):
        self.attrs = attrs or {}
        self.measurement_group_id = id
        super().__init__(id=id, location=location, interval=interval, default_tz=default_tz, design=design, **kwargs)

    @cached_property
    @abstractmethod
    def org_id(self) -> Optional[str]:
        raise NotImplementedError()

    @cached_property
    @abstractmethod
    def confidentiality(self) -> Confidentiality:
        raise NotImplementedError()

    @override
    def __repr__(self):
        response = self.__class__.__name__ + ' ' + self.measurement_group_id
        if 'location' in self:
            response += f' at {self.location}'
        if 'interval' in self:
            response += f' with interval {self.interval}'
        return response

    @override
    def copy(self: Self) -> Self:
        c = self.__class__(id=self.measurement_group_id)
        self._copy_self(c)
        return c

    @abstractmethod
    def measurement(self, subject: Any, name: Optional[str] = None) -> Any:
        raise NotImplementedError()

    @property
    @abstractmethod
    def resource_type_map(self) -> Mapping[str, ResourceRecord]:
        raise NotImplementedError()

    @cached_property
    def available_measurements(self) -> pd.DataFrame:
        # go through the resource_type_map and collect resource_type, start_date, end_date
        data = []

        has_names = False
        for record in self.resource_type_map.values():
            if record.get('name'):
                has_names = True
                break

        for record in self.resource_type_map.values():
            resource_type = record['resource_type']
            if resource_type in (str(R.fixed_design_spec), str(R.tracker_design_spec), str(R.location), str(R.interval)):
                continue
            start_date = record.get('min_timestamp')
            if start_date is not None:
                start_date = pd.Timestamp(start_date).tz_convert(self.default_tz)
            end_date = record.get('max_timestamp')
            if end_date is not None:
                end_date = pd.Timestamp(end_date).tz_convert(self.default_tz)
            freq = (record.get('attrs', {}) or {}).get('freq', '')
            row = {
                'resource_type': resource_type,
                'start_date': start_date,
                'end_date': end_date,
                'freq': freq,
            }
            if has_names:
                row['name'] = record.get('name', '')
            data.append(row)

        columns = ['resource_type', 'freq', 'start_date', 'end_date']
        index_def = 'resource_type'
        if has_names:
            columns.insert(1, 'name')
            index_def = ['resource_type', 'name']

        result = pd.DataFrame(data, columns=columns)
        if has_names:
            result['name'] = result['name'].astype(str).replace({'None': ''})
        result.sort_values(by=['resource_type'], inplace=True)
        result.set_index(index_def, inplace=True)
        result.replace({None: ''}, inplace=True)
        return result


class MeasurementGroup(AbstractMeasurementGroup):
    @cached_property
    @override
    def org_id(self) -> Optional[str]:
        return self.group_meta.get('org_id')

    @cached_property
    @override
    def confidentiality(self) -> Confidentiality:
        return self.group_meta['confidentiality']

    @cached_property
    def group_meta(self) -> GroupMeta:
        return PvradarClient.instance().get_json(
            Query(
                path=f'/measurements/groups/{self.measurement_group_id}',
                provider='dock',
            )
        )

    def __init__(
        self,
        id: str,
        *,
        location: Optional[Location | tuple | str] = None,
        interval: Optional[Any] = None,
        default_tz: Optional[str] = None,
        design: Optional[PvradarSiteDesign] = None,
        **kwargs,
    ):
        self.measurement_group_id = id
        lat = self.group_meta.get('lat')
        lon = self.group_meta.get('lon')
        if lat is not None and lon is not None:
            location = (lat, lon)
        utc_offset = self.group_meta.get('utc_offset')
        if utc_offset is not None:
            # TODO: Review: using pvlib's tz logic to prevent internal issues
            if utc_offset % 1 != 0:
                raise TypeError(
                    f'Floating-point tz has non-zero fractional part: {utc_offset}. Only whole-number offsets are supported.'
                )
            default_tz = f'Etc/GMT{-int(utc_offset):+d}'
        if self.group_meta['min_timestamp'] is not None and self.group_meta['max_timestamp'] is not None:
            try:
                interval = pd.Interval(
                    pd.Timestamp(self.group_meta['min_timestamp']),
                    pd.Timestamp(self.group_meta['max_timestamp']),
                    closed='both',
                )
            except Exception as e:
                raise PvradarSdkError(
                    f'failed to create interval from group meta {self.group_meta["min_timestamp"]} - {self.group_meta["max_timestamp"]}'
                ) from e

        self._resource_map = self._get_resource_map()

        if 'fixed_design_spec' in self._resource_map:
            fixed_design_spec_resource = self.measurement(R.fixed_design_spec)
            design = make_fixed_design(**fixed_design_spec_resource)
        elif 'tracker_design_spec' in self._resource_map:
            tracker_design_spec_resource = self.measurement('tracker_design_spec')
            design = make_tracker_design(**tracker_design_spec_resource)
        super().__init__(id=id, location=location, interval=interval, default_tz=default_tz, design=design, **kwargs)

    def _get_resource_map(self) -> Mapping[str, ResourceRecord]:
        parsed = PvradarClient.instance().get_json(
            Query(
                path=f'/measurements/groups/{self.measurement_group_id}/resources',
                provider='dock',
            )
        )
        result: dict[str, ResourceRecord] = {}
        for record in parsed['data']:
            key = record['resource_type'] + (f':{record["name"]}' if record.get('name') else '')
            result[key] = ResourceRecord(**record)
        return result

    @override
    def measurement(self, subject: Any, name: Optional[str] = None, label: Optional[str] = None) -> Any:
        if isinstance(subject, str):
            resource_type = subject
            user_requested_attrs = {'resource_type': resource_type}
        elif is_attrs_convertible(subject):
            user_requested_attrs = dict(attrs_as_descriptor_mapping(subject))
            resource_type = user_requested_attrs['resource_type']
        else:
            raise ValueError('Unsupported subject type: ' + str(subject))
        query_params = {}
        if name is not None:
            query_params['name'] = name
        resource = PvradarClient.instance().get_data_case(
            Query(
                path=f'/measurements/groups/{self.measurement_group_id}/resources/{resource_type}',
                provider='dock',
                params=query_params,
            )
        )
        resource = convert_by_attrs(resource, user_requested_attrs)
        if is_series_or_frame(resource):
            resource.attrs['measurement_group_id'] = self.measurement_group_id
            resource.attrs['label'] = label
        return resource

    @property
    @override
    def resource_type_map(self) -> Mapping[str, ResourceRecord]:
        return self._resource_map
