
class NotThreadSafe:
    from .dynamic_cache import CachedPropertyDependencyMixin
    from .dynamic_cache import dependent_cached_property


class ThreadSafe:
    from .dynamic_cache_thread_safe import CachedPropertyDependencyThreadSafeMixin
    from .dynamic_cache_thread_safe import dependent_cached_property_thread_safe
    from .dynamic_cache_thread_safe import thread_safe as thread_safe_inside_method
