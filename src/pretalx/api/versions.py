from rest_framework import exceptions

LEGACY = "LEGACY"
CURRENT_VERSION = LEGACY  # TODO: update to 2025.x
DEV_PREVIEW = "DEV_PREVIEW"

DEPRECATED_VERSIONS = []
CURRENT_VERSIONS = [
    LEGACY,
    CURRENT_VERSION,
    DEV_PREVIEW,
]
SUPPORTED_VERSIONS = CURRENT_VERSIONS + DEPRECATED_VERSIONS

# This list only exists for reporting and error messages, and is not used
# to provide any functionality.
UNSUPPORTED_VERSIONS = []

SERIALIZER_REGISTRY = {}


# We use a decorator around serializer classes to register them in the
# SERIALIZER_REGISTRY. This allows us to use the same serializer class for
# multiple versions of the API, by passing different versions but the same
# class_name to the decorator. (If no class_name is passed, the class.__name__ is
# used as the class_name.)
def register_serializer(versions=None, class_name=None):
    def inner_decorator(cls):
        nonlocal class_name, versions
        if not versions:
            versions = SUPPORTED_VERSIONS
        elif isinstance(versions, str):
            versions = [versions]
        class_name = class_name or cls.__name__
        for version in versions:
            SERIALIZER_REGISTRY[class_name, version] = cls
        return cls

    return inner_decorator


def get_serializer_by_version(name, version):
    return SERIALIZER_REGISTRY[name, version]


def get_api_version_from_request(request):
    if api_version := request.headers.get("pretalx-version"):
        if api_version not in SUPPORTED_VERSIONS:
            # TODO use special exception type
            raise exceptions.APIException(f"Unsupported version: {api_version}")

    if not api_version and request.auth.token:
        # TODO: fall back to token version
        # api_version = request.auth.token.api_version
        # if api_version not in SUPPORTED_VERSIONS:
        # raise exceptions.APIException(f"Unsupported version: {api_version}. Update your token: TODO docs url")
        pass

    if not api_version:
        api_version = CURRENT_VERSION
        if request.auth.token:
            # TODO: apply the current/latest version to the token and save it.
            pass
    # TODO: track use of legacy versions, send/show warning (once) to user
    return api_version
