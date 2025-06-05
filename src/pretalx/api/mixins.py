from rest_framework import exceptions

from pretalx.api.versions import get_api_version_from_request, get_serializer_by_version


class ApiVersionException(exceptions.APIException):
    status_code = 400
    default_detail = "API version not supported."
    default_code = "invalid_version"


class PretalxViewSetMixin:
    def get_versioned_serializer(self, name):
        try:
            version = get_api_version_from_request(self.request)
            return get_serializer_by_version(name, version)
        except KeyError:
            raise ApiVersionException()

    def get_serializer_class(self):
        if hasattr(self, "get_unversioned_serializer_class"):
            base_class = self.get_unversioned_serializer_class()
        elif hasattr(self, "serializer_class"):
            base_class = self.serializer_class
        elif hasattr(self, "serializer_class_name"):
            base_class = self.serializer_class_name

        if not isinstance(base_class, str):
            base_class = base_class.__name__

        return self.get_versioned_serializer(base_class)
