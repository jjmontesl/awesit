
def module_from_name(module):
    """
    Returns a class object from a class name.

    :param kls: Context qualified name of the class.
    :return: A class instance representing the given class.
    """

    try:
        m = __import__(module)
        return m
    except Exception as e:
        raise
        #raise ImportError("Error retrieving class by name '%s': %s" % (kls, e))


def class_from_name(kls):
    """
    Returns a class object from a class name.

    :param kls: Context qualified name of the class.
    :return: A class instance representing the given class.
    """

    try:
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m
    except Exception as e:
        raise
        #raise ImportError("Error retrieving class by name '%s': %s" % (kls, e))
