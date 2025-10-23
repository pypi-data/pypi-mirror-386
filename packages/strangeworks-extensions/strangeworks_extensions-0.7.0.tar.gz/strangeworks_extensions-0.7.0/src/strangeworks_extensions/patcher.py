"""patcher.py."""

import functools
import logging

logger = logging.getLogger(__name__)


def __logger(fn, *args, **kwargs):
    """Instrument Given Function/Method with a Logger.

    Any call to the function will generate a log entry with function name, and
    arguments. Take care to make sure no sensitive information is passed in
    with the arguments.

    Parameters
    ----------
    fn : function
        Function/class method to instrument.

    Returns
    -------
    Any | None:
        The value returned by the given function or method.
    """
    logger.info(f"[PATCHED] {fn.__name__} args={args}, kwargs={kwargs}")
    result = fn(*args, **kwargs)
    return result


def patch_function(module_name: str, function_name: str, wrapper_function=__logger):
    """Instrument given function.

    Parameters
    ----------
    module_name : str
        module where function resides
    function_name : str
        name of the function
    wrapper_function : _type_, optional
        wrapper function, by default __logger

    Returns
    -------
    _type_
        Function which is being instrumented. Useful if it is needed to rever to the
        original function at some point.
    """
    try:
        # Import the module
        module = __import__(module_name, fromlist=[""])

        # Get the original function
        original_function = getattr(module, function_name)

        # Create wrapper
        @functools.wraps(original_function)
        def wrapped_function(*args, **kwargs):
            return wrapper_function(original_function, *args, **kwargs)

        # Replace the function in the module
        setattr(module, function_name, wrapped_function)

        logger.debug(f"Patched {module_name}.{function_name}")
        return original_function

    except Exception as ex:
        print(f"Failed to patch {module_name}.{function_name}: {ex}")
        return None


def patch_class_method(module_name, class_name, method_name, wrapper_function=__logger):
    """Instrument Class Method.

    Uses standard import to find the class and then patches its method.
    Uses __import__ to handle complex import chains.
    """
    try:
        # import module, get class ...
        module = __import__(module_name, fromlist=[class_name])
        class_obj = getattr(module, class_name)

        # Get the original method
        original_method = getattr(class_obj, method_name)

        # Create a wrapper function
        @functools.wraps(original_method)
        def wrapped_method(self, *args, **kwargs):
            return wrapper_function(
                original_method.__get__(self, class_obj), *args, **kwargs
            )

        # Replace the method
        setattr(class_obj, method_name, wrapped_method)
        logger.debug(f"Patched {class_name}.{method_name}")

        return original_method
    except ModuleNotFoundError:
        # ignore ... ok if module not found
        ...
    except Exception as ex:
        logger.exception(f"Failed to patch {class_name}.{method_name}: {ex}")
        return None
