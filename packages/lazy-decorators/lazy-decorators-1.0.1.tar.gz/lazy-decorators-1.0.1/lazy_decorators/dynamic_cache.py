from functools import cached_property


'''
Warning:
    Any class uses the decorator @dependent_cached_property,
    MUST inherit CachedPropertyDependencyMixin"

Make sure to do that, the dependency functionality won't work if you don't
'''


class __InputTypeException(Exception):
    pass


class _DependentCachedProperty(cached_property):
    def __init__(self, func, depends_on):
        # Validate that depends_on is a list
        if not type(depends_on) is list:
            raise __InputTypeException('depends_on Must be a list')
        self.depends_on = depends_on
        
        # Save cache
        super().__init__(func)


def dependent_cached_property(depends_on):
    def wrapper(func):
        return _DependentCachedProperty(func, depends_on)
    return wrapper


class CachedPropertyDependencyMixin:
    
    def __setattr__(self, attr_name, value):
        super().__setattr__(attr_name, value)

        # Invalidate all dependent cached_propertis
        for key, attr_value in type(self).__dict__.items():
            if self._is_dependent_property(attr_value):
                is_depended = attr_name in attr_value.depends_on
                if is_depended:
                    self._delete_cache(key)
    
    @staticmethod
    def _is_dependent_property(attr_value):
        return isinstance(attr_value, _DependentCachedProperty)
    
    
    def _delete_cache(self, key):
        if key in self.__dict__:
            self.__dict__.pop(key, None)
    
    
    def invalidate_cache(self, *names):
        for name in names:
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
