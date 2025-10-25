from __future__ import annotations

import contextlib
import io
import pickle
import re
import sys
import warnings
from abc import ABCMeta
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from glob import glob
from inspect import Parameter, getfile, signature
from pathlib import Path
from shutil import copyfile
from traceback import format_exc, print_exception
from typing import Any, Callable, Hashable, Sequence, TypeVar

import makefun
import numpy as np
import pandas
import py
import regex
from bidict import bidict
from IPython import embed
from ruamel import yaml

from .io import get_params, pickle_dump, yaml_dump, yaml_load

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

Number = int | float | complex


R = TypeVar("R")

__all__ = [
    "add_extra_parameters",
    "capture_stderr",
    "cfmt",
    "cprint",
    "Crop",
    "Data",
    "df_join",
    "ErrorValue",
    "format_list",
    "get_config",
    "get_slice",
    "ipy_debug",
    "SliceKeepSize",
    "Struct",
    "warn",
    "wraps_combine",
]


@contextlib.contextmanager
def capture_stderr():
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            capture = py.io.StdCaptureFD(out=False, err=True, in_=False)  # noqa
            yield capture
        except Exception:
            raise Exception
        finally:
            capture.reset()


def wraps_combine(wrapper: Callable[[Any, ...], Any] | type, ignore: Sequence[str] = None) -> Callable[[Any, ...], R]:
    """decorator to combine arguments and doc strings of wrapped and wrapper functions,
    *args and/or **kwargs in wrapped will be replaced by the arguments from wrapper,
    duplicate arguments will be left in place in wrapped

    example:

    def wrapper(a, b, c, **kwargs):
        return a + b + c

    @wraps_combine(wrapper)
    def wrapped(a, d, e=45, *args, f=5, **kwargs):
        return d * e * wrapper(*args, **kwargs)

    signature: wrapped(a, d, e, b, c, *, f=5, **kwargs)
    """

    if ignore is None:
        ignore = []

    class WrapsException(Exception):
        pass

    def wrap(wrapped: Callable[[Any, ...], R]) -> Callable[[Any, ...], R]:
        if wrapped.__doc__ and wrapper.__doc__:
            doc = f"{wrapped.__doc__}\n\nwrapping {wrapper.__name__}:\n\n{wrapper.__doc__.lstrip(' ')}"
        elif wrapped.__doc__:
            doc = wrapped.__doc__
        elif wrapper.__doc__:
            doc = wrapper.__doc__
        else:
            doc = None

        try:
            try:
                sig_wrapper = signature(wrapper.__init__ if isinstance(wrapper, type) else wrapper)
                sig_wrapped = signature(wrapped.__init__ if isinstance(wrapped, type) else wrapped)
            except ValueError:
                raise WrapsException
            z = [(p, p.name, p.kind) for p in sig_wrapped.parameters.values()]
            p1, n1, k1 = zip(*z) if len(z) else ((), (), ())
            z = [
                (p, p.name, p.kind)
                for p in sig_wrapper.parameters.values()
                if (p.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD) or p.name not in n1)
                and p.name not in ignore
            ]
            p0, n0, k0 = zip(*z) if len(z) else ((), (), ())

            idx0a = k0.index(Parameter.VAR_POSITIONAL) if Parameter.VAR_POSITIONAL in k0 else None
            idx0k = k0.index(Parameter.VAR_KEYWORD) if Parameter.VAR_KEYWORD in k0 else None
            idx1a = k1.index(Parameter.VAR_POSITIONAL) if Parameter.VAR_POSITIONAL in k1 else None
            idx1k = k1.index(Parameter.VAR_KEYWORD) if Parameter.VAR_KEYWORD in k1 else None

            if idx1a is not None:
                if idx0a:
                    new_parameters = [Parameter(p.name, p.kind, annotation=p.annotation) for p in p1[:idx1a]]
                else:
                    new_parameters = list(p1[:idx1a])
                if len(new_parameters) == 0 or new_parameters[-1].default == Parameter.empty:
                    new_parameters.extend(p0[:idx0k])
                else:
                    new_parameters.extend(
                        [
                            Parameter(
                                p.name,
                                p.kind,
                                default="empty" if p.default == Parameter.empty else p.default,
                                annotation=p.annotation,
                            )
                            for p in p0[:idx0k]
                        ]
                    )
                new_parameters.extend(p1[idx1a + 1 : idx1k])
            elif idx1k is not None:
                if idx0a is not None:
                    new_parameters = list(p1[:idx1k])
                else:
                    new_parameters = [Parameter(p.name, p.kind, annotation=p.annotation) for p in p1[:idx1k]]
                new_parameters.extend(
                    [
                        Parameter(
                            p.name,
                            Parameter.KEYWORD_ONLY,
                            default="empty" if p.default == Parameter.empty else p.default,
                            annotation=p.annotation,
                        )
                        for p in p0[: (idx0k if idx0a is None else idx0a)]
                    ]
                )
            else:
                new_parameters = list(p1)
            if idx0k is not None:
                new_parameters.append(p0[idx0k])

            @makefun.wraps(wrapped, new_sig=sig_wrapper.replace(parameters=new_parameters), doc=doc)
            def fun(*args: Any, **kwargs: Any) -> R:
                return wrapped(*args, **kwargs)

        except WrapsException:

            @makefun.wraps(wrapped, doc=doc)
            def fun(*args: Any, **kwargs: Any) -> R:
                return wrapped(*args, **kwargs)

        except Exception:  # noqa
            warnings.warn(f"Exception annotating function {wrapped.__name__}:\n\n{format_exc()}")

            @makefun.wraps(wrapped, doc=doc)
            def fun(*args: Any, **kwargs: Any) -> R:
                return wrapped(*args, **kwargs)

        return fun

    return wrap  # type: ignore


class Struct(dict):
    """dict where the items are accessible as attributes"""

    key_pattern = regex.compile(r"(^(?=\d)|\W)")

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.update(*args, **kwargs)

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, key):
        if key not in self:
            raise AttributeError(key)
        return self[key]

    def __setitem__(self, key, value):
        super().__setitem__(self.transform_key(key), value)

    def __getitem__(self, key):
        return super().__getitem__(self.transform_key(key))

    def __contains__(self, key):
        return super().__contains__(self.transform_key(key))

    def __deepcopy__(self, memodict=None):
        cls = self.__class__
        copy = cls.__new__(cls)
        copy.update(**deepcopy(super(), memodict or {}))
        return copy

    def __dir__(self):
        return self.keys()

    def __missing__(self, key):
        return None

    @classmethod
    def transform_key(cls, key):
        return cls.key_pattern.sub("_", key) if isinstance(key, str) else key

    def copy(self):
        return self.__deepcopy__()

    def update(self, *args, **kwargs):
        for arg in args:
            if hasattr(arg, "keys"):
                for key, value in arg.items():
                    self[key] = value
            else:
                for key, value in arg:
                    self[key] = value
        for key, value in kwargs.items():
            self[key] = value


yaml.RoundTripRepresenter.add_representer(Struct, yaml.RoundTripRepresenter.represent_dict)


@dataclass
class ErrorValue:
    """format a value and its error with equal significance
    example f'value = {ErrorValue(1.23234, 0.34463):.2g}'
    """

    value: Number
    error: Number

    def __format__(self, format_spec: str) -> str:
        notation = regex.findall(r"[efgEFG]", format_spec)
        notation = notation[0] if notation else "f"
        value_str = f"{self.value:{format_spec}}"
        digits = regex.findall(r"\d+", format_spec)
        if digits:
            digits = int(digits[0])
        else:
            frac_part = regex.findall(r"\.(\d+)", value_str)
            digits = len(frac_part[0]) if frac_part else 0
        if notation in "gG":
            int_part = regex.findall(r"^[-+]?(\d+)", value_str)
            if int_part:
                digits -= len(int_part[0])
            frac_part = regex.findall(r"\.(\d+)", value_str)
            if frac_part:
                zeros = regex.findall(r"^0+", frac_part[0])
                if zeros:
                    digits += len(zeros[0])
        exp = regex.findall(r"[eE]([-+]?\d+)$", value_str)
        exp = int(exp[0]) if exp else 0
        error_str = f"{round(self.error * 10**-exp, digits):{f'.{digits}f'}}"
        split = regex.findall(r"([^eE]+)([eE][^eE]+)", value_str)
        if split:
            return f"({split[0][0]}±{error_str}){split[0][1]}"
        else:
            return f"{value_str}±{error_str}"

    def __str__(self) -> str:
        return f"{self}"

    def __mul__(self, other: ErrorValue | Number) -> ErrorValue:
        if isinstance(other, ErrorValue):
            return ErrorValue(
                self.value * other.value,
                np.sqrt(abs(self.value) ** 2 * other.error**2 + abs(other.value) ** 2 * self.error**2),
            )
        else:
            return ErrorValue(self.value * other, self.error * other)

    def __truediv__(self, other) -> ErrorValue:
        if isinstance(other, ErrorValue):
            return ErrorValue(
                self.value / other.value,
                np.sqrt(
                    abs(1 / other.value) ** 2 * self.error**2 + abs(self.value / other.value**2) ** 2 * self.error**2
                ),
            )
        else:
            return ErrorValue(self.value / other, self.error / other)

    def __add__(self, other: ErrorValue | Number) -> ErrorValue:
        if isinstance(other, ErrorValue):
            return ErrorValue(self.value + other.value, np.sqrt(self.error**2 + other.error**2))
        else:
            return ErrorValue(self.value + other, self.error)

    def __sub__(self, other: ErrorValue | Number) -> ErrorValue:
        if isinstance(other, ErrorValue):
            return ErrorValue(self.value - other.value, np.sqrt(self.error**2 + other.error**2))
        else:
            return ErrorValue(self.value - other, self.error)


def cfmt(string: str) -> str:
    """format a string for color printing, see cprint"""
    pattern = regex.compile(r"(?:^|[^\\])(?:\\\\)*(<)((?:(?:\\\\)*\\<|[^<])*?)(:)([^:]*?[^:\\](?:\\\\)*)(>)")
    fmt_split = regex.compile(r"(?:^|\W?)([a-zA-Z]|\d+)?")
    str_sub = regex.compile(r"(?:^|\\)((?:\\\\)*[<>])")

    # noinspection PyShadowingNames
    def format_fmt(fmt: str) -> str:
        f = fmt_split.findall(fmt)[:3]
        color, decoration, background = f + [""] * max(0, (3 - len(f)))

        t = "KRGYBMCWargybmcwk"
        d = {"b": 1, "u": 4, "r": 7}
        text = ""
        if len(color):
            if color.isnumeric() and 0 <= int(color) <= 255:
                text = f"\033[38;5;{color}m{text}"
            elif not color.isnumeric() and color in t:
                text = f"\033[38;5;{t.index(color)}m{text}"
        if len(background):
            if background.isnumeric() and 0 <= int(background) <= 255:
                text = f"\033[48;5;{background}m{text}"
            elif not background.isnumeric() and background in t:
                text = f"\033[48;5;{t.index(background)}m{text}"
        if len(decoration) and decoration.lower() in d:
            text = f"\033[{d[decoration.lower()]}m{text}"
        return text

    while matches := pattern.findall(string, overlapped=True):
        for match in matches:
            fmt = format_fmt(match[3])
            sub_string = match[1].replace("\x1b[0m", f"\x1b[0m{fmt}")
            string = string.replace("".join(match), f"{fmt}{sub_string}\033[0m")
    return str_sub.sub(r"\1", string)


@wraps_combine(print)
def cprint(*args, **kwargs):
    """print colored text
    text between <> is colored, escape using \\ to print <>
    text and color format in <> is separated using : and text color, decoration and background color are separated
    using . or any character not a letter, digit or :
    colors: 'krgybmcw' (darker if capitalized) or terminal color codes (int up to 255)
    decorations: b: bold, u: underlined, r: swap color with background color"""
    print(*(cfmt(arg) for arg in args), **kwargs)


@wraps(warnings.warn)
def warn(message: str, category: type = None, stacklevel: int = 1, source: Any = None) -> None:
    warnings.warn(cfmt(f"<{message}:208>"), category, stacklevel + 1, source)


def format_list(string: str, lst: Sequence, fmt: str = None) -> str:
    """format a list in a grammatically correct way
    example: format_list('in {channel|channels}: {}', (1, 2, 5))
        'in channels: 1, 2 and 5'
    """
    if fmt is None:
        fmt = ""
    string = string.replace("{}", "{0}")
    plurals = re.findall(r"{([^|{}]+)\|([^|{}]+)}", string)
    for i, option in enumerate(plurals, start=1):
        string = string.replace(f"{{{option[0]}|{option[1]}}}", f"{{{i}}}")
    if len(lst) == 1:
        return string.format(f"{lst[0]:{fmt}}", *[option[0] for option in plurals])
    else:
        return string.format(
            ", ".join([f"{i:{fmt}}" for i in lst[:-1]]) + f" and {lst[-1]:{fmt}}",
            *[option[1] for option in plurals],
        )


def ipy_debug():
    """Enter ipython after an exception occurs any time after executing this."""

    def excepthook(etype, value, traceback):
        print_exception(etype, value, traceback)
        embed(colors="neutral")

    sys.excepthook = excepthook


def get_slice(shape, n):
    ndim = len(shape)
    if isinstance(n, type(Ellipsis)):
        n = [None] * ndim
    elif not isinstance(n, (tuple, list)):
        n = [n]
    else:
        n = list(n)
    ell = [i for i, e in enumerate(n) if isinstance(e, type(Ellipsis))]
    if len(ell) > 1:
        raise IndexError("an index can only have a single ellipsis (...)")
    if len(ell):
        if len(n) > ndim:
            n.remove(Ellipsis)  # type: ignore
        else:
            n[ell[0]] = None
            while len(n) < ndim:
                n.insert(ell[0], None)
    while len(n) < ndim:
        n.append(None)

    pad = []
    for i, (e, s) in enumerate(zip(n, shape)):
        if e is None:
            e = slice(None)
        elif isinstance(e, Number):
            e = slice(e, e + 1)
        if isinstance(e, (slice, range)):
            start = int(np.floor(0 if e.start is None else e.start))
            stop = int(np.ceil(s if e.stop is None else e.stop))
            step = round(1 if e.step is None else e.step)
            if step != 1:
                raise NotImplementedError("step sizes other than 1 are not implemented!")
            pad.append((max(0, -start) // step, max(0, stop - s) // step))
            if start < 0:
                start = 0
            elif start >= s:
                start = s
            if stop >= s:
                stop = s
            elif stop < 0:
                stop = 0
            n[i] = slice(start, stop, step)  # type: ignore
        else:
            a = np.asarray(n[i])
            if not np.all(a[:-1] <= a[1:]):
                raise NotImplementedError("unsorted slicing arrays are not supported")
            n[i] = a[(0 <= a) * (a < s)]  # type: ignore
            pad.append((sum(a < 0), sum(a >= s)))

    return n, pad


@dataclass
class Crop:
    """Special crop object which never takes data from outside the array, and returns the used extent too,
    together with an image showing how much of each pixel is within the extent,
    negative indices are taken literally, they do not refer to the end of the dimension!
    """

    array: np.ndarray

    def __getitem__(self, n):
        n = get_slice(self.array.shape, n)[0]
        return np.vstack([(i.start, i.stop) for i in n]), self.array[tuple(n)]  # type: ignore


@dataclass
class SliceKeepSize:
    """Guarantees the size of the slice by filling with a default value,
    negative indices are taken literally, they do not refer to the end of the dimension!
    """

    array: np.ndarray
    default: Number = 0

    def __getitem__(self, n):
        n, pad = get_slice(self.array.shape, n)
        crop = self.array[tuple(n)]
        default = self.default(crop) if callable(self.default) else self.default
        return np.pad(crop, pad, constant_values=default)  # type: ignore

    def __setitem__(self, n, value):
        n = np.vstack(n)
        idx = np.prod([(0 < i) & (i < s) for i, s in zip(n, self.array.shape)], 0) > 0
        if not isinstance(value, Number):
            value = np.asarray(value)[idx]
        if n.size:
            self.array[tuple(n[:, idx])] = value


class Data(metaclass=ABCMeta):
    params = None
    do_not_pickle = ()
    channels: bidict
    colors: bidict

    def __init__(self) -> None:
        self.stage = set()
        self.runtime = datetime.now().strftime("%Y%m%d_%H%M%S")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        self.error = format_exc()
        self.save()

    @classmethod
    def load(cls, file: Path | str) -> Self:
        files = glob(str(file))
        if len(files) == 0:
            raise FileNotFoundError
        file = Path(max(files)).resolve()
        with open(file, "rb") as f:
            new = pickle.load(f)
        new.__class__ = cls
        new.file = file
        return new

    @staticmethod
    def stage_rec(fun: Callable) -> Callable:
        def wrap(self, *args, **kwargs):
            res = fun(self, *args, **kwargs)
            self.stage.add(fun.__name__)
            return res

        return wrap

    def save(self, file: Path | str = None) -> None:
        if file is None and hasattr(self, "folder_out"):
            file = self.folder_out / f"{self.__class__.__name__.lower()}_{self.runtime}.pickle"
        if file is not None:
            pickle_dump(self, file)  # type: ignore

    @classmethod
    def load_from_parameter_file(cls, parameter_file: Path | str) -> Self:
        parameter_file = Path(parameter_file)
        params = getParams(parameter_file.with_suffix(".yml"), required=({"paths": ("folder_out",)},))
        if Path(params["paths"]["folder_out"]).exists():
            pickles = [
                file
                for file in Path(params["paths"]["folder_out"]).iterdir()
                if file.name.startswith(f"{cls.__name__.lower()}_") and file.suffix == ".pickle"
            ]
        else:
            pickles = None
        if not pickles:
            raise FileNotFoundError(
                f"No files matching {Path(params['paths']['folder_out']) / f'{cls.__name__.lower()}_*.pickle'}"
            )
        return cls.load(max(pickles))

    def run(self) -> None:
        self.runtime = datetime.now().strftime("%Y%m%d_%H%M%S")

    def clean(self) -> None:
        if Path(self.params["paths"]["folder_out"]).exists():
            pickles = [
                file
                for file in Path(self.params["paths"]["folder_out"]).iterdir()
                if file.name.startswith(f"{self.__class__.__name__.lower()}_") and file.suffix == ".pickle"
            ]
            if pickles:
                pickles.remove(max(pickles))
                for pkl in pickles:
                    pkl.unlink()

    def color(self, color_or_channel: int | str) -> str:
        return color_or_channel if isinstance(color_or_channel, str) else self.channels[color_or_channel]

    def channel(self, color_or_channel: int | str) -> int:
        return self.colors[color_or_channel] if isinstance(color_or_channel, str) else color_or_channel

    @classmethod
    def get_template_file(cls) -> Path:
        return Path(getfile(cls).replace(".py", "_parameters_template.yml"))

    @classmethod
    def copy_template_file(cls) -> None:
        source = cls.get_template_file()
        cwd = Path.cwd()
        stem = source.stem
        suffix = source.suffix
        dest = cwd / source.name

        i = 0
        while dest.exists():
            i += 1
            dest = cwd / f"{stem}_{i}{suffix}"

        copyfile(source, dest)

    @classmethod
    def update_parameter_file(cls, parameter_file: str | Path) -> None:
        parameter_file = Path(parameter_file)
        new_parameter_file = parameter_file.parent / f"{parameter_file.stem}_updated.yml"
        if new_parameter_file.exists():
            raise FileExistsError(f"File {new_parameter_file} already exists.")
        else:
            template = cls.get_template_file()
            yaml_dump(
                get_params(
                    template,
                    parameter_file,
                    replace_values=True,
                    template_file_is_parent=True,
                    compare=True,
                    warn=False,
                ),
                new_parameter_file,
                unformat=True,
            )


def df_join(h: pandas.DataFrame) -> pandas.DataFrame:
    """join DataFrames given by the first indices of h on the other indices"""
    groups = h.groupby(level=0)
    n = len(groups)
    df, j = None, None
    for a, (i, g) in enumerate(groups):
        if a == 0:
            df = g.droplevel(0)
        elif a == n - 1:
            return df.join(g.droplevel(0), lsuffix=f"_{j:.0f}", rsuffix=f"_{i:.0f}")
        else:
            df = df.join(g.droplevel(0), lsuffix=f"_{j:.0f}")
        j = i
    return df


def add_extra_parameters(parameters: dict[Hashable, Any], extra_parameters: dict[Hashable, Any]) -> None:
    for key, value in extra_parameters.items():
        if isinstance(value, dict):
            add_extra_parameters(parameters[key], value)
        else:
            parameters[key] = value


get_config = yaml_load
getConfig = get_config
getParams = get_params
objFromDict = Struct
