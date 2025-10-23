from django.utils import timezone
from dm_core.redis.service import cache_read
from datetime import datetime


class DMDateTime(object):

    @staticmethod
    def yyyymmdd_hhmmss_from_isoformat(iso_time: str) -> str:
        """
        Return ISO formatted Datetime string to YYYYMMDDhhmmss format
        """
        return datetime.fromisoformat(iso_time).strftime('%Y%m%d%H%M%S')

    @staticmethod
    def datetime_from_isoformat(iso_time: str) -> datetime:
        """
        Convert ISO Formatted Date Time String to Date Time object
        """
        return datetime.fromisoformat(iso_time)

    @staticmethod
    def datetime_to_isoformat(dt_object: datetime) -> str:
        """
        Return Date Time object to ISO formatted Date Time string
        """
        return dt_object.strftime('%Y-%m-%dT%H:%M:%S.%f%z')

    @staticmethod
    def now(pre_set_id=None) -> datetime:
        """
        Generic wrapper to retrieve current system time in UTC

        pre_set_id is set by integration test to retrieve the time of choice
        """
        if pre_set_id is None:
            return timezone.now()
        return DateTime()._current_time(cache_key=pre_set_id)

    @cache_read('time.now')
    def _current_time(self, **kwargs) -> datetime:
        """
        _current_time : Used for integration testing purposes only
        """
        if 'cache_data' in kwargs and kwargs['cache_data'] is not None:
            if type(kwargs['cache_data']) == datetime:
                return kwargs['cache_data']
            return self.datetime_from_isoformat(kwargs['cache_data'])
        return timezone.now()
