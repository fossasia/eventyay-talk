from i18nfield.fields import I18nCharField, I18nTextField
from i18nfield.rest_framework import I18nField
from rest_flex_fields import is_expanded
from rest_framework import exceptions
from rest_framework.serializers import ModelSerializer

from pretalx.api.versions import get_api_version_from_request, get_serializer_by_version


class ApiVersionException(exceptions.APIException):
    status_code = 400
    default_detail = "API version not supported."
    default_code = "invalid_version"


class PretalxViewSetMixin:
    endpoint = None
    logtype_map = {
        "create": ".create",
        "update": ".update",
        "partial_update": ".update",
    }

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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if locale := self.request.GET.get("locale"):
            if locale in self.request.event.locales:
                context["override_locale"] = locale
        return context

    def perform_create(self, serializer):
        super().perform_create(serializer)
        if self.logtype_map and (action := self.logtype_map.get(self.action)):
            serializer.instance.log_action(action, person=self.request.user, orga=True)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        if self.logtype_map and (action := self.logtype_map.get(self.action)):
            serializer.instance.log_action(action, person=self.request.user, orga=True)

    def perform_destroy(self, instance):
        parent = getattr(instance, "log_parent", None)
        super().perform_destroy(instance)
        if (
            parent
            and self.logtype_map
            and (action := self.logtype_map.get(self.action))
        ):
            parent.log_action(action, person=self.request.user, orga=True)

    def has_perm(self, permission, obj=None):
        model = getattr(self, "model", None) or self.queryset.model
        permission_name = model.get_perm(permission)
        # request.event is not present when building API docs
        obj = obj or getattr(self.request, "event", None)
        return self.request.user.has_perm(permission_name, obj)

    def check_expanded_fields(self, *args):
        return [arg for arg in args if is_expanded(self.request, arg)]


class PlainI18nField(I18nField):
    def to_representation(self, value):
        return str(value)


class PretalxSerializer(ModelSerializer):
    """
    This serializer class will behave like the i18nfield serializer,
    outputting a dict/object for internationalized strings, unless if
    when it was initialized with an ``override_locale`` (taken from
    a URL queryparam, usually), in which case the string will be cast
    to the locale in question – relying on either a view or a middleware
    to apply the locale manager.
    """

    def __init__(self, *args, **kwargs):
        self.override_locale = kwargs.get("context", {}).get("override_locale")
        super().__init__(*args, **kwargs)
        if self.override_locale:
            self.serializer_field_mapping[I18nCharField] = PlainI18nField
            self.serializer_field_mapping[I18nTextField] = PlainI18nField


PretalxSerializer.serializer_field_mapping[I18nCharField] = I18nField
PretalxSerializer.serializer_field_mapping[I18nTextField] = I18nField
