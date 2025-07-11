import warnings

from django.core.cache import CacheKeyWarning

# We do not support memcached, suppress key warnings
warnings.simplefilter("ignore", CacheKeyWarning)
