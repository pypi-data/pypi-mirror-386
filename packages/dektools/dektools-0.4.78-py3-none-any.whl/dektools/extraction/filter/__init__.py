import re
import json
import logging
from collections import OrderedDict
from functools import partial, reduce
from jsonpath_ng import parse
from ...module import ModuleProxy
from ...hash import hash_file
from ...re import re2args
from ...time import now, DateTime
from ...str import startswith, endswith, triple_find, hex_random, Fragment
from ...dict import merge_mro_dict, is_dict
from ...attr import DeepObjectCall
from ...context.utils import Method, MethodSimple, AttrProxy
from ...py import get_inner_vars
from ..base.value import ProxyValue


class FilterSet:
    custom_filters = {}

    @staticmethod
    def inner_eval(s):
        return eval(s, get_inner_vars('__inner_filter_context__'))

    def __init__(self, context=None):
        context = merge_mro_dict(self.__class__, 'custom_filters', (context or {}) | default_filters)
        self.context = {k: DeepObjectCall(v) if is_dict(v) else v for k, v in context.items()}

    def raw_eval(self, *args, **kwargs):
        return eval(*args, **kwargs)

    def register(self, key, func):
        if isinstance(func, str):
            func = self.raw_eval(func, self.context)
        self.context[key] = func
        return func

    def update(self, context):
        for k, v in context.items():
            self.register(k, v)

    def eval(self, context, value, expressions):
        cursor = value
        if cursor is ProxyValue.NOT_EXIST:
            if _assert_exist_name in expressions:
                _assert_exist(cursor, tips=expressions)
            return cursor
        if context:
            context = self.context | context
        else:
            context = self.context
        __inner_filter_context__ = context  # noqa
        for expression in expressions:
            func = self.raw_eval(expression, __inner_filter_context__)
            cursor = func(cursor)
            if cursor is ProxyValue.NOT_EXIST:
                if _assert_exist_name in expressions:
                    _assert_exist(cursor, tips=expressions)
                return cursor
        return cursor


def __list_at(default, index):
    def wrapper(x):
        if x:
            return x[index]
        else:
            return default

    return wrapper


def __last(default=None):
    return __list_at(default, -1)


def __first(default=None):
    return __list_at(default, 0)


def __printf(trans=None):
    def inner(value):
        val = value
        if trans:
            val = trans(value)
        print(val)
        return value

    return inner


def __split(s, sep=" ", strip=True, none=False):
    result = []
    for x in re.split(sep, s):
        if strip:
            x = x.strip()
        if none or x:
            result.append(x)
    return result


def __bytes(x):
    if isinstance(x, str):
        return x.encode('utf-8')
    elif isinstance(x, bytes):
        return x
    else:
        return __bytes(json.dumps(x, sort_keys=True))


def __jpl(*xx):
    def inner(yy):
        r = []
        for y in yy:
            for x in xx:
                dl = parse(x).find(y)
                if dl:
                    r.append(dl[0].value)
                    break
        return r

    return inner


_default_value = object()
_assert_exist_name = 'ae'


def _assert_exist(x, tips=None):
    if x is ProxyValue.NOT_EXIST:
        raise ValueError(f'Get a NOT_EXIST value. {tips if tips else ""}')
    return x


def _encode(encoding='utf-8', errors='ignore'):
    def inner(x):
        if isinstance(x, (list, tuple, set)):
            return x.__class__(inner(y) for y in x)
        return x.encode(encoding, errors)

    return inner


def _decode(encoding='utf-8', errors='ignore'):
    def inner(x):
        if isinstance(x, (list, tuple, set)):
            return x.__class__(inner(y) for y in x)
        return x.decode(encoding, errors)

    return inner


turn_empty = object()


def _turn(value, src, dst=turn_empty):
    result = turn_empty
    if isinstance(src, dict):
        r = src.get(value, dst)
        if r is not turn_empty:
            result =  r
    elif isinstance(src, (list, tuple, set)):
        if value in src:
            result = dst
    else:
        if src == value:
            result = dst
    if result is not turn_empty:
        return result(value) if callable(result) else result
    return value


class _Frag:
    def __init__(self, *seps):
        self._seps = seps
        self._item = None
        self._sep = False

    def __getitem__(self, item):
        self._item = item
        return self

    @property
    def sep(self):
        self._sep = True
        return self

    def __call__(self, s):
        return Fragment(s, *self._seps, sep=self._sep)[self._item]


logger = logging.getLogger(__name__)

default_filters = {
    'c': lambda x: x(),
    'me': lambda x: x,
    'mp': ModuleProxy(),
    _assert_exist_name: _assert_exist,
    'print': lambda x, *args, **kwargs: print(x, *args, **kwargs) or x,
    'prints': lambda x, *args, **kwargs: lambda value: print(value, x, *args, **kwargs) or value,
    'log': lambda x: logger.debug(x) or x,
    'logs': lambda x: lambda value: logger.debug(f"{value} {x}") or value,
    'printf': __printf,
    'p': partial,
    'h': hash_file,
    'bs': __bytes,
    'hr': hex_random,
    'rh': lambda x: lambda s: s[len(x):] if s.startswith(x) else s,
    'rt': lambda x: lambda s: s[:-len(x)] if s.endswith(x) else s,
    'frag': _Frag,
    'reduce': reduce,
    'first': __first,
    'last': __last,
    'default': lambda x: (lambda y: y or x),
    'none': lambda x: x or None,
    'turn': lambda src, dst=None: lambda x: _turn(x, src, dst),
    'ne': lambda x: (None if x is ProxyValue.NOT_EXIST else x),
    'now': now,
    'date': lambda *fl, tz=None: lambda value: DateTime(tz).from_x(value, *fl),
    'daterf': lambda a, b: lambda x: DateTime.reformat(x, a, b),
    'orv': lambda x=None: lambda value: value or x,
    'split': lambda sep=" ", strip=True, none=False: lambda value: __split(value, sep, strip, none),
    's': lambda x: str(x),
    'm': Method(),
    'mm': MethodSimple(),
    'a': AttrProxy(),
    'lrd': lambda x: list(OrderedDict.fromkeys(x)),
    're': lambda pattern: lambda string: re2args(pattern, string),
    'ints': lambda x: x.__class__(int(y) for y in x),
    'at': lambda index, default=_default_value: (
        lambda array: default if (index < 0 or index >= len(array)) and default is not _default_value else array[
            index]),
    'sl': lambda begin=None, end=None, step=None: (lambda array: array[slice(begin, end, step)]),
    'sumd': lambda x: reduce(lambda y, z: y | z, x, {}),
    'jp': lambda x: (lambda y: parse(x).find(y)[0].value),
    'jpl': __jpl,
    'sw': startswith,
    'ew': endswith,
    'tf': lambda f, ll, r: lambda x: triple_find(x, f, ll, r),
    'en': _encode,
    'de': _decode,
}
