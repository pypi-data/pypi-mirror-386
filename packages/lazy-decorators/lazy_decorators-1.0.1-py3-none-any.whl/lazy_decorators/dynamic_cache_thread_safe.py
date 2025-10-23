from functools import cached_property, wraps
from threading import RLock


def thread_safe(func):
    
    _lock: RLock = RLock()
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        with _lock:
            return func(*args, **kwargs)
    return wrapper


'''
WARNING:
    Any class uses the decorator @dependent_cached_property_thread_safe,
    MUST inherit CachedPropertyDependencyThreadSafeMixin
    
Make sure to do that, the dependency functionality won't work if you don't.

WARNING:
    Use @thread_safe decorator under the @dependent_cached_property_thread_safe decorator
    If don't, inside of the property function won't be threadsafe
    
Do it EXACTLY like the how_to_use file. (As the decorator orders in the example)
'''


class __InputTypeException(Exception):
    pass


class _DependentCachedProperty(cached_property):
    _lock: RLock = RLock()
    
    def __init__(self, func, depends_on):
        # Validate that depends_on is a list
        if not type(depends_on) is list:
            raise __InputTypeException('depends_on Must be a list')
        self.depends_on = depends_on
        
        # Save cache with lock
        with self._lock:
            super().__init__(func)


def dependent_cached_property_thread_safe(depends_on):
    def wrapper(func):
        return _DependentCachedProperty(func, depends_on)
    return wrapper


class CachedPropertyDependencyThreadSafeMixin:
    _lock: RLock = RLock()
    
    def __setattr__(self, attr_name, value):
        super().__setattr__(attr_name, value)

        # Invalidate all dependent cached_propertis
        for key, attr_value in type(self).__dict__.items():
            if self._is_dependent_property(attr_value):
                is_depended = attr_name in attr_value.depends_on
                if is_depended:
                    self._delete_cache_with_thread_lock(key)
    
    @staticmethod
    def _is_dependent_property(attr_value):
        return isinstance(attr_value, _DependentCachedProperty)
    
    
    def _delete_cache_with_thread_lock(self, key):
        with self._lock:
            if key in self.__dict__:
                self.__dict__.pop(key, None)
    
    
    def invalidate_cache(self, *names):
        for name in names:
            with self._lock:
                self._check_attr_exists(name)
                self._invalidate_one_cache(name)
    
    
    def _check_attr_exists(self, attr_name):
        if attr_name not in type(self).__dict__:
            raise Exception(f'AttibuteError: {self.__class__} has no attribute: "{attr_name}"')
    
    
    def _invalidate_one_cache(self, attr_name):
        # Invalidate cached property manually
        attr_value = type(self).__dict__[attr_name]
        if isinstance(attr_value, _DependentCachedProperty) or isinstance(attr_value, cached_property):
            self.__dict__.pop(attr_name, None)
