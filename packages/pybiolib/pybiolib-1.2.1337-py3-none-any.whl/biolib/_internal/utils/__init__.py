import time
import uuid
from fnmatch import fnmatch

from biolib.biolib_binary_format.utils import LazyLoadedFile
from biolib.typing_utils import Callable, List, Union, cast

PathFilter = Union[str, Callable[[str], bool]]


def filter_lazy_loaded_files(files: List[LazyLoadedFile], path_filter: PathFilter) -> List[LazyLoadedFile]:
    if not (isinstance(path_filter, str) or callable(path_filter)):
        raise Exception('Expected path_filter to be a string or a function')

    if callable(path_filter):
        return list(filter(lambda x: path_filter(x.path), files))  # type: ignore

    glob_filter = cast(str, path_filter)

    # since all file paths start with /, make sure filter does too
    if not glob_filter.startswith('/'):
        glob_filter = '/' + glob_filter

    def _filter_function(file: LazyLoadedFile) -> bool:
        return fnmatch(file.path, glob_filter)

    return list(filter(_filter_function, files))


def open_browser_window_from_notebook(url_to_open: str) -> None:
    try:
        from IPython.display import (  # type:ignore # pylint: disable=import-error, import-outside-toplevel
            Javascript,
            display,
            update_display,
        )
    except ImportError as error:
        raise Exception('Unexpected environment. This function can only be called from a notebook.') from error

    display_id = str(uuid.uuid4())
    display(Javascript(f'window.open("{url_to_open}");'), display_id=display_id)
    time.sleep(1)
    update_display(Javascript(''), display_id=display_id)
