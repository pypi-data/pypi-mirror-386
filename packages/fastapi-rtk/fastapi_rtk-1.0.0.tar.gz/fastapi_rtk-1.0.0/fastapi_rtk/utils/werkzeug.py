import sys

__all__ = ["import_string", "ImportStringError"]


class ImportStringError(ImportError):
    """
    COPIED FROM WERKZEUG LIBRARY

    Provides information about a failed :func:`import_string` attempt.
    """

    #: String in dotted notation that failed to be imported.
    import_name: str
    #: Wrapped exception.
    exception: BaseException

    def __init__(self, import_name: str, exception: BaseException) -> None:
        self.import_name = import_name
        self.exception = exception
        msg = import_name
        name = ""
        tracked = []
        for part in import_name.replace(":", ".").split("."):
            name = f"{name}.{part}" if name else part
            imported = import_string(name, silent=True)
            if imported:
                tracked.append((name, getattr(imported, "__file__", None)))
            else:
                track = [f"- {n!r} found in {i!r}." for n, i in tracked]
                track.append(f"- {name!r} not found.")
                track_str = "\n".join(track)
                msg = (
                    f"import_string() failed for {import_name!r}. Possible reasons"
                    f" are:\n\n"
                    "- missing __init__.py in a package;\n"
                    "- package or module path not included in sys.path;\n"
                    "- duplicated package or module name taking precedence in"
                    " sys.path;\n"
                    "- missing module, class, function or variable;\n\n"
                    f"Debugged import:\n\n{track_str}\n\n"
                    f"Original exception:\n\n{type(exception).__name__}: {exception}"
                )
                break

        super().__init__(msg)

    def __repr__(self) -> str:
        return f"<{type(self).__name__}({self.import_name!r}, {self.exception!r})>"


def import_string(import_name: str, silent: bool = False):
    """
    COPIED FROM WERKZEUG LIBRARY

    Imports an object based on a string.  This is useful if you want to
    use import paths as endpoints or something similar.  An import path can
    be specified either in dotted notation (``xml.sax.saxutils.escape``)
    or with a colon as object delimiter (``xml.sax.saxutils:escape``).

    If `silent` is True the return value will be `None` if the import fails.

    :param import_name: the dotted name for the object to import.
    :param silent: if set to `True` import errors are ignored and
                   `None` is returned instead.
    :return: imported object
    """
    import_name = import_name.replace(":", ".")
    try:
        try:
            __import__(import_name)
        except ImportError:
            if "." not in import_name:
                raise
        else:
            return sys.modules[import_name]

        module_name, obj_name = import_name.rsplit(".", 1)
        module = __import__(module_name, globals(), locals(), [obj_name])
        try:
            return getattr(module, obj_name)
        except AttributeError as e:
            raise ImportError(e) from None

    except ImportError as e:
        if not silent:
            raise ImportStringError(import_name, e).with_traceback(
                sys.exc_info()[2]
            ) from None

    return None
