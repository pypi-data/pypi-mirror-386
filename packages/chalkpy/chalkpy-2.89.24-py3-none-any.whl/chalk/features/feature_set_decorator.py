# pyright: reportPrivateUsage = false

from __future__ import annotations

import ast
import builtins
import collections
import copy
import inspect
import re
import sys
import textwrap
import types
import typing
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Type, TypeVar, Union, cast, overload

import pyarrow as pa

from chalk._lsp.error_builder import FeatureClassErrorBuilder, LSPErrorBuilder
from chalk.features import is_features_cls
from chalk.features._class_property import classproperty, classproperty_support
from chalk.features._encoding.pyarrow import pyarrow_to_primitive
from chalk.features.dataframe._impl import DataFrameMeta
from chalk.features.feature_field import Feature, VersionInfo
from chalk.features.feature_set import ClassSource, Features, CURRENT_FEATURE_REGISTRY
from chalk.features.feature_time import feature_time
from chalk.features.feature_wrapper import FeatureWrapper, unwrap_feature
from chalk.features.namespace_context import build_namespaced_name
from chalk.features.tag import Tags
from chalk.features.underscore import Underscore
from chalk.serialization.parsed_annotation import ParsedAnnotation
from chalk.streams import Windowed
from chalk.streams._windows import GroupByWindowed, get_name_with_duration
from chalk.utils import notebook
from chalk.utils.collections import ensure_tuple
from chalk.utils.duration import Duration, parse_chalk_duration, parse_chalk_duration_s
from chalk.utils.metaprogramming import MISSING, set_new_attribute
from chalk.utils.string import to_snake_case
from chalk.stores.online_store_config import OnlineStoreConfig

from chalk.features.feature_cache_strategy import (
    CacheStrategy,
    CacheNullsType,
    CacheDefaultsType,
    get_cache_settings_from_strategy,
    get_cache_strategy_from_cache_settings,
)

T = TypeVar("T")

GENERATED_OBSERVED_AT_NAME = "__chalk_observed_at__"

__all__ = ["features"]


@overload
def features(
    *,
    owner: Optional[str] = None,
    tags: Optional[Tags] = None,
    etl_offline_to_online: bool = False,
    max_staleness: Optional[Duration] = None,
    name: Optional[str] = None,
    singleton: bool = False,
    cache_nulls: CacheNullsType = True,
    cache_defaults: CacheDefaultsType = True,
) -> Callable[[Type[T]], Type[T]]: ...


@overload
def features(cls: Type[T]) -> Type[T]: ...


def features(
    cls: Optional[Type[T]] = None,
    *,
    owner: Optional[str] = None,
    tags: Optional[Tags] = None,
    etl_offline_to_online: bool = False,
    max_staleness: Optional[Duration] = None,
    name: Optional[str] = None,
    singleton: bool = False,
    online_store_config: Optional[OnlineStoreConfig] = None,
    cache_nulls: CacheNullsType = True,
    cache_defaults: CacheDefaultsType = True,
) -> Union[Callable[[Type[T]], Type[T]], Type[T]]:
    """Chalk lets you spell out your features directly in Python.

    Features are namespaced to a `FeatureSet`.
    To create a new `FeatureSet`, apply the `@features`
    decorator to a Python class with typed attributes.
    A `FeatureSet` is constructed and functions much like
    Python's own `dataclass`.

    Parameters
    ----------
    owner
        The individual or team responsible for these features.
        The Chalk Dashboard will display this field, and alerts
        can be routed to owners.
    tags
        Added metadata for features for use in filtering, aggregations,
        and visualizations. For example, you can use tags to assign
        features to a team and find all features for a given team.
    etl_offline_to_online
        When `True`, Chalk copies this feature into the online environment
        when it is computed in offline resolvers.
        Setting `etl_offline_to_online` on a feature class assigns it to all features on the
        class which do not explicitly specify `etl_offline_to_online`.
    max_staleness
        When a feature is expensive or slow to compute, you may wish to cache its value.
        Chalk uses the terminology "maximum staleness" to describe how recently a feature
        value needs to have been computed to be returned without re-running a resolver.
        Assigning a `max_staleness` to the feature class assigns it to all features on the
        class which do not explicitly specify a `max_staleness` value of their own.
    cache_nulls
        When `True` (default), Chalk will cache all values, including nulls.
        When `False`, Chalk will not update the null entry in the cache.
        When `"evict_nulls"`, Chalk will evict the entry that would have been
        null from the cache, if it exists.

        Concretely, suppose the current state of a database is `{a: 1, b: 2}`,
        and you write a row `{a: 2, b: None}`. Here is the expected result in the db:
            - `{a: 2, b: None}` when `cache_nulls=True` (default)
            - `{a: 2, b: 2}` when `cache_nulls=False`
            - `{a: 2}` when `cache_nulls="evict_nulls"`
    cache_defaults
        When `True` (default), Chalk will cache all values, including default values.
        When `False`, Chalk will not update the default entry in the cache.
        When `"evict_defaults"`, Chalk will evict the entry that would have been
        a default value from the cache, if it exists.

        Concretely, suppose the current state of a database is `{a: 1, b: 2}`,
        and you write a row `{a: 2, b: "default"}`, and the default value for feature b is `"default"`.
        Here is the expected result in the db:
            - `{a: 2, b: "default"}` when `cache_defaults=True`
            - `{a: 2, b: 2}` when `cache_defaults=False`
            - `{a: 2}` when `cache_defaults="evict_defaults"`

        The `cache_nulls` and `cache_defaults` options can be used together on the same feature with the
        following exceptions: if `cache_nulls=False`, then `cache_defaults` cannot be `"evict_defaults"`, and if
        `cache_nulls="evict_defaults"`, then `cache_defaults` cannot be `False`.
    Other Parameters
    ----------------
    cls
        The decorated class. You shouldn't need to pass this argument.
    name
        The name for the feature set. By default, the name of a feature is
        taken from the name of the attribute on the class, prefixed with
        the camel-cased name of the class.
    singleton
        If `True`, the feature set is a singleton, and there will be only
        one instance of the class. Because there is only one instance, a
        singleton feature class does not have a primary key. Features
        defined on a singleton feature class are available in all resolvers,
        regardless of whatever other features are used as inputs to the resolver.

    Examples
    --------
    >>> from chalk.features import features
    >>> @features(
    ...     owner="andy@chalk.ai",
    ...     max_staleness="30m",
    ...     etl_offline_to_online=True,
    ...     tags="user-group",
    ... )
    ... class User:
    ...     id: str
    ...     # Comments here appear in the web!
    ...     # :tags: pii
    ...     name: str | None
    ...     # :owner: userteam@mycompany.com
    ...     location: LatLng
    """

    def wrap(c: Type[T]) -> Type[T]:
        namespace = name if name is not None else to_snake_case(c.__name__)
        namespace = build_namespaced_name(name=namespace)

        source_info = ClassSource(c)

        error_builder = FeatureClassErrorBuilder(
            uri=source_info.filename if source_info.filename is not None else "__main__",
            namespace=namespace,
            node=source_info and source_info.tree,
        )
        nonlocal max_staleness
        if name is not None and re.sub(r"[^a-z_0-9]", "", namespace) != namespace:
            error_builder.add_diagnostic(
                message=(
                    f"Namespace must be composed of lower-case alpha-numeric characters and '_'. Provided namespace "
                    f"'{namespace}' for class '{c.__name__}' contains invalid characters."
                ),
                code="11",
                label="invalid namespace",
                range=error_builder.decorator_kwarg_value_range(kwarg="name") or error_builder.class_definition_range(),
                raise_error=ValueError,
            )

        if name is not None and len(namespace) == 0:
            error_builder.add_diagnostic(
                message=f"Namespace cannot be an empty string, but is for the class '{c.__name__}'.",
                label="empty name",
                code="12",
                range=error_builder.decorator_kwarg_value_range(kwarg="name") or error_builder.class_definition_range(),
                raise_error=ValueError,
            )

        if max_staleness is None:
            max_staleness = timedelta(0)
        else:
            try:
                max_staleness = parse_chalk_duration(max_staleness)
            except ValueError as e:
                error_builder.add_diagnostic(
                    message=f"Invalid 'max_staleness'. {e.args[0]}",
                    label=f"invalid duration {max_staleness}",
                    range=error_builder.decorator_kwarg_value_range(kwarg="max_staleness"),
                    raise_error=ValueError,
                    code="13",
                )

        cache_strategy = get_cache_strategy_from_cache_settings(
            cache_nulls=cache_nulls,
            cache_defaults=cache_defaults
        )

        registry = CURRENT_FEATURE_REGISTRY.get()
        registry_features = registry.get_feature_sets()
        previous_features_class = registry_features.get(namespace, None)

        if (
            previous_features_class is not None
            and not notebook.is_notebook()
            and source_info.tree is not None
            and previous_features_class.__chalk_source_info__.tree is not None
            and (
                source_info.filename != previous_features_class.__chalk_source_info__.filename
                or source_info.tree.lineno != previous_features_class.__chalk_source_info__.tree.lineno
                or source_info.class_source != previous_features_class.__chalk_source_info__.class_source
            )
        ):
            error_builder.add_diagnostic(
                message=(
                    f"Feature class '{previous_features_class.__name__}' is defined twice: "
                    f"once in '{c.__module__}' and once in '{previous_features_class.__module__}'."
                ),
                code="14",
                label="duplicate class",
                range=error_builder.decorator_kwarg_value_range("name") or error_builder.class_definition_range(),
                raise_error=ValueError,
            )

        if (
            notebook.is_notebook()
            and previous_features_class is not None
            and notebook.is_defined_in_module(previous_features_class)
        ):
            # Not generating an LSP here because we're in a notebook anyway
            # TODO: See if we can pretty-print lsp errors in notebooks, at which point we can generate one that points to the old feature class
            raise ValueError(
                f"Cannot re-define feature class '{previous_features_class.__name__}' in a notebook: it was previously defined in '{previous_features_class.__module__}'."
            )

        updated_class = _process_class(
            cls=c,
            source_info=source_info,
            error_builder=error_builder,
            owner=owner,
            tags=ensure_tuple(tags),
            etl_offline_to_online=etl_offline_to_online,
            max_staleness=max_staleness,
            cache_strategy=cache_strategy,
            namespace=namespace,
            singleton=singleton,
            online_store_config=online_store_config,
        )
        assert is_features_cls(updated_class)

        registry.add_feature_set(updated_class)
        return cast(Type[T], updated_class)

    # See if we're being called as @features or @features().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @features without parens.
    return wrap(cls)


def _discover_feature(
    fs: Sequence[Feature],
    name: str,
    *conditions: Callable[[Feature], bool],
) -> Optional[Feature]:
    """
    Parameters
    ----------
    fs
        The features to search
    name
        Used for error messages
    conditions
        Tested in order. The first feature that matches _any_ condition is returned.
    """
    for cond in conditions:
        filtered_features = [c for c in fs if cond(c)]

        if len(filtered_features) == 1:
            return filtered_features[0]

        if len(filtered_features) > 1:
            assert filtered_features[0].features_cls is not None
            representative = filtered_features[0]
            assert representative.features_cls is not None
            b = representative.lsp_error_builder.add_diagnostic(
                message=(
                    f"Multiple {name} features are not supported in {representative.features_cls.__name__}: "
                    + ", ".join(f"{representative.features_cls.__name__}.{x.name}" for x in filtered_features)
                ),
                code="51",
                label=f"duplicate {name} feature",
                range=representative.lsp_error_builder.property_range(representative.attribute_name),
                raise_error=ValueError,
            )

            for ff in filtered_features[1:]:
                b.with_range(
                    range=ff.lsp_error_builder.property_range(ff.attribute_name),
                    label=f"duplicate {name} feature",
                )

    return None


def _setattr_fn(bidirectional_alias: Mapping[str, str]):
    def setattr(self: object, key: str, value: object):
        if key in bidirectional_alias:
            super(self.__class__, self).__setattr__(bidirectional_alias[key], value)
        return super(self.__class__, self).__setattr__(key, value)

    setattr.__name__ = "__setattr__"
    return setattr


def _getattribute_fn(self: object, attribute_name: str):
    # If calling getattr() on an instance for a feature name,
    # do NOT return a class-level FeatureWrapper.
    # Instead, raise an attribute error
    o = object.__getattribute__(self, attribute_name)
    if isinstance(o, FeatureWrapper):
        raise AttributeError(
            f"Feature '{attribute_name}' is not defined on this instance of class'{type(self).__name__}'"
        )
    return o


_getattribute_fn.__name__ = "__getattribute__"


def _init_fn(
    additional_inits: frozenset[str],
    alias_from_to: Mapping[str, str],
):
    def _init(self: Features, /, *args: object, **kwargs: object):
        for feat, val in zip(self.features, args):
            if feat.attribute_name in kwargs:
                raise ValueError(
                    f"Argument '{feat.attribute_name}' cannot be specified as both a positional and keyword argument"
                )
            kwargs[feat.attribute_name] = val

        for from_, to in alias_from_to.items():
            if from_ in kwargs and to in kwargs:
                raise ValueError(
                    f"The features '{from_}' and '{to}' are aliases of each other. Only one can be specified, but both were given."
                )
            if to in kwargs:
                kwargs[from_] = kwargs[to]
        assert self.__chalk_ts__ is not None
        ts_feature_name = self.__chalk_ts__.attribute_name

        for k, v in kwargs.items():
            actual_key = k
            if "@" in k:
                base_name, version_str = k.rsplit("@", 1)
                try:
                    version = int(version_str)
                    actual_key = f"{base_name}_v{version}"
                    if not hasattr(self.__class__, actual_key):
                        actual_key = base_name
                except ValueError:
                    pass

            cls_field = getattr(self.__class__, actual_key, None)
            if type(cls_field) is not FeatureWrapper and actual_key not in additional_inits and actual_key != ts_feature_name:
                raise TypeError(f"{self.__class__.__name__}.__init__() got an unexpected keyword argument '{k}'")

            setattr(self, actual_key, v)

    _init.__name__ = "__init__"
    return _init


def _parse_tags(ts: str) -> List[str]:
    ts = re.sub(",", " ", ts)
    ts = re.sub(" +", " ", ts.strip())
    return [xx.strip() for xx in ts.split(" ")]


def _get_field(
    cls: Type,
    error_builder: FeatureClassErrorBuilder,
    annotation_name: str,
    comments: Mapping[str, str],
    class_owner: Optional[str],
    class_tags: Optional[Tuple[str, ...]],
    class_etl_offline_to_online: bool,
    class_max_staleness: timedelta,
    namespace: str,
    is_singleton: bool,
    class_cache_strategy: CacheStrategy = CacheStrategy.ALL,
) -> Feature:
    # Return a Field object for this field name and type.  ClassVars and
    # InitVars are also returned, but marked as such (see f._field_type).
    # default_kw_only is the value of kw_only to use if there isn't a field()
    # that defines it.

    # If the default value isn't derived from Field, then it's only a
    # normal default value.  Convert it to a Field().
    last_value = LSPErrorBuilder.lsp
    LSPErrorBuilder.lsp = False
    default = getattr(cls, annotation_name, ...)
    LSPErrorBuilder.lsp = last_value

    if isinstance(default, Feature):
        # The feature was set like x: int = feature(...)
        f = default
        if f.unversioned_attribute_name is None and not f.is_autogenerated:
            f.unversioned_attribute_name = annotation_name
        if f.version is not None:
            f.version.base_name = f.name if f.is_name_set() else annotation_name
            f.name = f.version.name_for_version(f.version.default)
        if f.is_name_set():
            if "." in f.name:
                error_builder.add_diagnostic(
                    message=(
                        f"Custom feature names cannot contain a dot, but the feature '{f.name}' on the class '{cls.__name__}' includes a dot. You might consider using a has-one feature instead."
                    ),
                    code="75",
                    label="dotted name",
                    range=error_builder.property_value_kwarg_range(annotation_name, kwarg="name")
                    or error_builder.property_range(annotation_name),
                    raise_error=ValueError,
                )
            elif " " in f.name:
                error_builder.add_diagnostic(
                    message=(
                        f"Custom feature names cannot contain spaces, but the feature '{f.name}' on the class '{cls.__name__}' includes a space."
                    ),
                    code="75",
                    label="name with space",
                    range=error_builder.property_value_kwarg_range(annotation_name, kwarg="name")
                    or error_builder.property_range(annotation_name),
                    raise_error=ValueError,
                )

    elif isinstance(default, Windowed):
        # The feature was set like x: Windowed[int] = windowed()
        # Convert it to a Feature
        try:
            f = default._to_feature(bucket=None)
        except Exception as e:
            error_builder.add_diagnostic(
                message=f"Invalid window found for feature '{namespace}.{annotation_name}'. {e}",
                label="invalid duration",
                code="18",
                range=error_builder.property_value_range(annotation_name),
                raise_error=ValueError,
            )
            f = default
        if f.version is not None:
            f.version.base_name = f.name if f.is_name_set() else annotation_name
            f.name = f.version.name_for_version(f.version.default)

    else:
        underscore_expression = None
        # The feature was not set explicitly
        if isinstance(default, types.MemberDescriptorType):
            # This is a field in __slots__, so it has no default value.
            default = ...
        if isinstance(default, Underscore):
            underscore_expression = default
            default = ...

        f = Feature(
            name=annotation_name,
            namespace=namespace,
            default=default,
            underscore_expression=underscore_expression,
        )

    # Only at this point do we know the name and the type.  Set them.
    f.namespace = namespace

    if not f.is_typ_set():
        f.typ = ParsedAnnotation(cls, annotation_name)

    f.features_cls = cls
    f.attribute_name = annotation_name
    if not hasattr(f, "name"):
        f.name = annotation_name
    f.is_singleton = is_singleton

    _process_field(
        f=f,
        comments=comments,
        class_owner=class_owner,
        class_tags=class_tags,
        class_etl_offline_to_online=class_etl_offline_to_online,
        class_max_staleness=class_max_staleness,
        class_cache_strategy=class_cache_strategy,
        error_builder=error_builder,
    )
    return f


def _process_field(
    f: Feature,
    comments: Mapping[str, str],
    class_owner: Optional[str],
    class_tags: Optional[Tuple[str, ...]],
    class_etl_offline_to_online: bool,
    class_max_staleness: timedelta,
    error_builder: FeatureClassErrorBuilder,
    class_cache_strategy: CacheStrategy = CacheStrategy.ALL,
) -> Feature:
    comment_for_feature = comments.get(f.attribute_name)
    comment_based_description = None
    comment_based_owner = None
    comment_based_tags = None

    if comment_for_feature is not None:
        comment_lines = []
        for line in comment_for_feature.splitlines():
            stripped_line = line.strip()
            if stripped_line.startswith(":owner:"):
                comment_based_owner = stripped_line.removeprefix(":owner:").strip()
            elif stripped_line.startswith(":tags:"):
                parsed = _parse_tags(stripped_line.removeprefix(":tags:"))
                if len(parsed) > 0:
                    if comment_based_tags is None:
                        comment_based_tags = parsed
                    else:
                        comment_based_tags.extend(parsed)
            else:
                comment_lines.append(line)

        comment_based_description = "\n".join(comment_lines)

    if f.description is None and comment_based_description:
        f.description = comment_based_description

    if comment_based_tags is not None:
        if f.tags is None:
            f.tags = comment_based_tags
        else:
            f.tags.extend(comment_based_tags)

    if class_tags is not None:
        if f.tags is None:
            f.tags = list(class_tags)
        else:
            f.tags.extend(class_tags)

    if f.owner is not None and comment_based_owner is not None:
        assert f.features_cls is not None
        error_builder.add_diagnostic(
            message=(
                f"Owner for feature '{f.name}' on class '{f.features_cls.__name__}' "
                f"specified both on the feature and in the comment. Please use only one of these two."
            ),
            code="15",
            label="second declaration",
            range=error_builder.property_value_kwarg_range(f.attribute_name, kwarg="owner")
            or error_builder.property_range(f.attribute_name),
            raise_error=ValueError,
        )

    elif f.owner is None:
        f.owner = comment_based_owner or class_owner

    # The attribute is not defined if the feature intends to use the class default
    if not hasattr(f, "max_staleness"):
        f.max_staleness = class_max_staleness

    f_cache_nulls, f_cache_defaults = get_cache_settings_from_strategy(f.cache_strategy)
    class_cache_nulls, class_cache_defaults =  get_cache_settings_from_strategy(class_cache_strategy)

    f.cache_strategy = get_cache_strategy_from_cache_settings(
        cache_nulls= f_cache_nulls if f_cache_nulls is not None else class_cache_nulls,
        cache_defaults= f_cache_defaults if f_cache_defaults is not None else class_cache_defaults,
    )

    # Using the private variable because the etl_offline_to_online is a read-only property
    if not hasattr(f, "etl_offline_to_online"):
        f.etl_offline_to_online = class_etl_offline_to_online
    return f


def _repr_fn(self: Features):
    parts: list[str] = []
    for f in self.features:
        val = getattr(self, f.attribute_name, MISSING)
        if val is not MISSING:
            parts.append(f"{f.attribute_name}={val!r}")
    return f"{self.__class__.__name__}(" + ", ".join(parts) + ")"


_repr_fn.__name__ = "__repr__"


def _eq_fn(self: Features, other: object):
    if not isinstance(other, type(self)):
        return NotImplemented
    return all(
        getattr(self, f.attribute_name, MISSING) == getattr(other, f.attribute_name, MISSING) for f in self.features
    )


_eq_fn.__name__ = "__eq__"


def _len_fn(self: Features):
    count = 0
    for f in self.features:
        if not f.no_display and hasattr(self, f.attribute_name):
            count += 1
    return count


_len_fn.__name__ = "__len__"


def _items_fn(self: Features):
    for f in self.features:
        if not f.no_display and hasattr(self, f.attribute_name):
            yield f.fqn, getattr(self, f.attribute_name)


_items_fn.__name__ = "__items__"


def _iter_fn(self: Features):
    for f in self.features:
        if (
            hasattr(self, f.attribute_name)
            and type(f).__name__ == "Feature"
            and not f.is_has_one
            and not f.is_has_many
            and not f.no_display
        ):
            yield f.fqn, getattr(self, f.attribute_name)


_iter_fn.__name__ = "__iter__"


def _parse_annotation_comments(source_info: ClassSource, cls_annotations: Dict[str, Any]) -> Mapping[str, str]:
    if source_info.tree is None or source_info.dedent_source is None:
        return {}

    source_lines = source_info.dedent_source.splitlines()
    """ Get rid of the decorator, if exists (python 3.8 won't have one)"""
    for i, line in enumerate(source_lines):
        if line.lstrip().startswith("class "):
            source_lines = source_lines[i:]
            break

    comments_for_annotations: Dict[str, str] = {}

    for stmt in source_info.tree.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            line = stmt.lineno - source_info.tree.lineno - 1
            comments: List[str] = []
            while line >= 0 and source_lines[line].strip().startswith("#"):
                comment = source_lines[line].strip().lstrip("#").strip()
                comments.insert(0, comment)
                line -= 1

            if len(comments) > 0:
                comments_for_annotations[stmt.target.id] = textwrap.dedent("\n".join(comments))

    """Attach the same comments to windowed features as well"""
    for annotation, feature_type in cls_annotations.items():
        if annotation in comments_for_annotations and isinstance(feature_type, Windowed):
            for bucket_size in feature_type.buckets_seconds:
                pseudofeature_name = get_name_with_duration(annotation, bucket_size)
                comments_for_annotations[pseudofeature_name] = comments_for_annotations[annotation]

    return comments_for_annotations


CHALK_SINGLETON_VALUE = 111


def _process_group_by_windowed(
    cls: Type,
    namespace: str,
    attribute_name: str,
    gbw: GroupByWindowed,
    cls_annotations: Dict[str, Any],
    error_builder: FeatureClassErrorBuilder,
) -> Feature:
    if gbw._name is None:
        gbw._name = gbw._name if gbw._name is not None else attribute_name

    gbw._namespace = namespace

    if gbw._dtype is not None:
        gbw._kind = pyarrow_to_primitive(gbw._dtype, name=attribute_name)
        if gbw._kind not in (int, float):
            error_builder.add_diagnostic(
                message=(
                    f"group_by_window feature '{namespace}.{attribute_name}' has an invalid dtype '{gbw._dtype}'. "
                    "Please use a numeric integer or float dtype, like 'int64' or 'float64'."
                ),
                label="invalid dtype",
                range=error_builder.property_value_kwarg_range(attribute_name, kwarg="dtype")
                or error_builder.property_value_range(attribute_name)
                or error_builder.property_range(attribute_name),
                code="16",
            )
    else:
        gbw._dtype = pa.float32()
        gbw._kind = float

    return Feature(
        name=gbw._name,
        attribute_name=attribute_name,
        namespace=namespace,
        features_cls=cls,
        typ=gbw._kind,
        version=None,
        default_version=1,
        description=gbw._description,
        owner=gbw._owner,
        tags=gbw._tags,
        primary=False,
        default=gbw._default,
        underscore_expression=gbw._expression,
        max_staleness=None,
        cache_strategy=CacheStrategy.ALL,
        etl_offline_to_online=None,
        encoder=None,
        decoder=None,
        pyarrow_dtype=gbw._dtype,
        join=None,
        is_feature_time=False,
        is_autogenerated=False,
        validations=None,
        all_validations=None,
        window_durations=tuple(),  # Not here, but on group by windowed
        window_duration=None,
        no_display=False,
        offline_ttl=None,
        last_for=None,
        hook=None,
        is_distance_pseudofeature=False,
        is_pseudofeature=False,
        window_materialization=gbw._materialization,
        group_by_windowed=gbw,
    )


_skip_attrs = {
    "__dict__",
    "__class__",
    "__annotations__",
    "__delattr__",
    "__dir__",
    "__doc__",
    "__eq__",
    "__format__",
    "__ge__",
    "__getattribute__",
    "__gt__",
    "__hash__",
    "__init__",
}


def _process_class(
    cls: Type[T],
    source_info: ClassSource,
    error_builder: FeatureClassErrorBuilder,
    owner: Optional[str],
    tags: Tuple[str, ...],
    etl_offline_to_online: bool,
    max_staleness: timedelta,
    namespace: str,
    singleton: bool,
    online_store_config: Optional[OnlineStoreConfig],
    cache_strategy: CacheStrategy = CacheStrategy.ALL,
) -> Type[T]:
    raw_cls_annotations = cls.__dict__.get("__annotations__", {})

    alias_from_to: Dict[str, str] = {}
    additional_inits: list[str] = []

    materialized_windows: list[Feature] = []
    group_by_materialized_windows: list[Feature] = []
    expression_windows: List[Feature] = []
    cls_annotations: Dict[str, Any] = {}

    if online_store_config is not None:
        online_store_config.feature_set_namespaces.add(namespace)

    for name, annotation in raw_cls_annotations.items():
        if name in ("features", "namespace", "items", "is_near"):
            error_builder.add_diagnostic(
                message=f"Feature '{name}' on class '{cls.__name__}' uses a reserved name.",
                label=f"reserved name '{name}'",
                range=error_builder.property_range(name),
                raise_error=TypeError,
                code="16",
            )

        if isinstance(annotation, Windowed) or (isinstance(annotation, str) and "Windowed" in annotation):
            # NOTE: For Windowed resolvers, both the Annotation and the value are instances of
            # Windowed, unlike normal features whose annotation is the underlying type, and the
            # value is an instance of FeatureWrapper. So both `annotation` and `wind` should be
            # instances of Windowed.
            #
            # In the future, we should use a subclass of Windowed, rather than an instance, for
            # the type annotation, similar to what we do for Features.
            if isinstance(annotation, str) and "Windowed" in annotation:
                try:
                    annotation = parse_quoted_window_feature(annotation, cls.__module__)
                except Exception as e:
                    error_builder.add_diagnostic(
                        message=(
                            f"Quoted Windowed feature type annotation '{annotation}' for '{namespace}.{name}' could not be parsed: {e}."
                            f"To create a windowed feature with quotes for typing, use "
                            f'\'{name}: "Windowed[int]" = windowed("10m", ...)\''
                        ),
                        label="missing windowed(...) call",
                        range=error_builder.property_range(name),
                        raise_error=TypeError,
                        code="17",
                    )
            assert isinstance(annotation, Windowed), f"failed to parse annotation {annotation} as Windowed"

            wind = getattr(cls, name, None)
            if wind is None or not isinstance(wind, Windowed):
                assert annotation._kind is not None
                error_builder.add_diagnostic(
                    message=(
                        f"Windowed feature '{namespace}.{name}' is missing windows. "
                        f"To create a windowed feature, use "
                        f"'{name}: Windowed[{annotation.kind.__name__}] = windowed(\"10m\", ...)'"
                    ),
                    label="missing windowed(...) call",
                    range=error_builder.property_range(name),
                    raise_error=TypeError,
                    code="17",
                )

            wind.kind = annotation.kind
            if wind._name is None:
                wind._name = name
            annotation._buckets = wind._buckets
            if len(wind._buckets) == 0:
                error_builder.add_diagnostic(
                    message=(
                        f"Windowed feature '{namespace}.{name}' does not have any window durations. "
                        f"To create a windowed feature, use "
                        f'\'{name}: Windowed[{annotation.kind.__name__}] = windowed("1h", "1d"))\''
                    ),
                    label="missing window durations",
                    range=error_builder.property_value_range(name) or error_builder.property_range(name),
                    code="777",
                )

            if isinstance(wind._materialization, dict):

                def get_mat_range():
                    return (
                        error_builder.property_value_kwarg_range(name, kwarg="materialization")
                        or error_builder.property_value_range(name)
                        or error_builder.property_range(name)
                    )

                if wind._expression is None:
                    error_builder.add_diagnostic(
                        message=(
                            f"Windowed feature '{namespace}.{name}' has a materialization, but no expression. "
                            f"To create a materialized windowed feature, use "
                            f"'{name}: Windowed[{annotation.kind.__name__}] = windowed(\"10m\", materialization={wind._materialization}, expression=_.your_dataframe_feature[_.field_to_agg].sum())'"
                        ),
                        label="materialization config",
                        range=get_mat_range(),
                        code="177",
                    )

                bucket_duration_raw = wind._materialization.get("bucket_duration", None)
                if bucket_duration_raw is not None:
                    try:
                        wind._materialization["bucket_duration"] = parse_chalk_duration(bucket_duration_raw)
                    except ValueError as e:
                        error_builder.add_diagnostic(
                            message=(
                                f"Windowed feature '{namespace}.{name}' has an invalid `bucket_duration`. {e.args[0]}"
                            ),
                            label="invalid duration",
                            range=get_mat_range(),
                            code="18",
                        )

                validated_bucket_durations: dict[Duration, list[Duration]] = collections.defaultdict(list)
                for d, windows_or_window in wind._materialization.get("bucket_durations", {}).items():
                    try:
                        d = parse_chalk_duration(d)
                    except ValueError as e:
                        error_builder.add_diagnostic(
                            message=(
                                f"Windowed feature '{namespace}.{name}' has an invalid key in `bucket_durations`. {e.args[0]}"
                            ),
                            label="invalid duration",
                            range=get_mat_range(),
                            code="18",
                            raise_error=ValueError,
                        )

                    for_windows = ensure_tuple(windows_or_window)
                    for w in for_windows:
                        try:
                            w = parse_chalk_duration(w)
                        except ValueError as e:
                            error_builder.add_diagnostic(
                                message=(
                                    f"Windowed feature '{namespace}.{name}' has an invalid key in `bucket_durations`. {e.args[0]}"
                                ),
                                label="invalid duration",
                                range=get_mat_range(),
                                code="18",
                                raise_error=ValueError,
                            )
                        validated_bucket_durations[d].append(w)

                wind._materialization["bucket_durations"] = validated_bucket_durations
                if bucket_duration_raw is None and not validated_bucket_durations:
                    error_builder.add_diagnostic(
                        message=(
                            f"Windowed feature '{namespace}.{name}' has a materialization, but no 'bucket_duration'. "
                            "Please provide a 'bucket_duration', like '1h', in the dictionary under the keyword "
                            "argument 'materialization'."
                        ),
                        label="missing 'bucket_duration' key",
                        range=get_mat_range(),
                        code="188",
                    )

            for bucket in wind._buckets:
                # Make pseudo-features for each bucket of the window
                try:
                    bucket_seconds = parse_chalk_duration_s(bucket)
                except ValueError as e:
                    # set bucket_seconds to anything so that we can continue accumulating errors
                    # in the class.
                    bucket_seconds = 60
                    error_builder.add_diagnostic(
                        message=f"Invalid window found for feature '{namespace}.{name}'. {e.args[0]}",
                        label="invalid duration",
                        range=error_builder.property_value_range(name),
                        code="18",
                    )

                try:
                    feat = wind._to_feature(bucket=bucket_seconds)
                except ValueError as e:
                    error_builder.add_diagnostic(
                        message=f"Invalid window found for feature '{namespace}.{name}'. {e.args[0]}",
                        label="invalid duration",
                        range=error_builder.property_value_range(name),
                        code="18",
                    )
                    continue

                if feat.window_materialization is not None:
                    materialized_windows.append(feat)
                elif feat.underscore_expression is not None:
                    expression_windows.append(feat)

                # For the pseudo-features, which track an individual bucket,
                # the correct annotation is the underlying annotation, not
                # Windowed[underlying], since it's only one value
                cls_annotations[feat.name] = wind.kind
                setattr(cls, feat.name, feat)
                if isinstance(bucket, str):  # pyright: ignore [reportUnnecessaryIsInstance] -- user provided
                    alias = f"{name}_{bucket}"
                    additional_inits.append(alias)
                    alias_from_to[
                        get_name_with_duration(
                            name_or_fqn=name,
                            duration="all" if bucket == "infinity" or bucket == "all" else bucket_seconds,
                        )
                    ] = alias

        windowed_group_by = getattr(cls, name, None)
        if isinstance(annotation, DataFrameMeta) and isinstance(windowed_group_by, GroupByWindowed):
            feat = _process_group_by_windowed(
                cls=cls,
                namespace=namespace,
                attribute_name=name,
                gbw=windowed_group_by,
                cls_annotations=cls_annotations,
                error_builder=error_builder,
            )
            group_by_materialized_windows.append(feat)
            setattr(cls, name, feat)
            kind = windowed_group_by._kind
            cls_annotations[name] = kind
        else:
            cls_annotations[name] = annotation

    _globals = sys.modules[cls.__module__].__dict__ if cls.__module__ in sys.modules else {}

    for name, member in inspect.getmembers(cls):
        if name in _skip_attrs:
            continue
        if name not in cls_annotations and isinstance(member, Windowed):
            error_builder.add_diagnostic(
                range=error_builder.property_range(name),
                message=f"Windowed feature '{namespace}.{name}' is missing an annotation, like 'Windowed[str]'",
                label="missing annotation",
                raise_error=TypeError,
                code="20",
            )

        # Feature times that weren't annotated.
        if name not in cls_annotations and isinstance(member, Feature):
            # All feature types need annotations, except for datetimes, which we can automatically infer
            if member._is_feature_time:
                # We must read the private variable to avoid parsing the annotation,
                # which might contain forward references that are not yet loaded
                cls_annotations[name] = datetime
            else:
                error_builder.add_diagnostic(
                    code="18",
                    range=error_builder.property_range(name),
                    message=f"Feature '{namespace}.{name}' is missing an annotation. Please add one, like '{name}: str = ...'",
                    label="missing annotation",
                    raise_error=TypeError,
                )
        if name not in cls_annotations and isinstance(member, str) and not name.startswith("__"):
            error_builder.add_diagnostic(
                code="18",
                range=error_builder.property_range(name),
                message=(
                    f"Feature '{namespace}.{name}' is missing an annotation. Did you use an equals sign instead of a colon? "
                    f"If so, please change your feature definition to '{name}: {member}'"
                ),
                label="missing annotation",
                raise_error=TypeError,
            )

        if name not in cls_annotations and isinstance(member, Underscore):
            error_builder.add_diagnostic(
                code="18",
                range=error_builder.property_range(name),
                message=f"Underscore feature '{namespace}.{name}' is missing an annotation. Please add one, like '{name}: int = ...'",
                label="missing annotation",
                raise_error=TypeError,
            )

        # catch malformed features like num_transactions: int = windowed("2h") with no Windowed type
        if isinstance(member, Windowed) and not isinstance(cls_annotations.get(name), Windowed):
            error_builder.add_diagnostic(
                message=(
                    f"Feature '{namespace}.{name}' is marked as 'windowed()', "
                    f"but also needs to be marked as a Windowed type. "
                    f"Please add one, like '{name}: Windowed[int] = ...'"
                ),
                range=error_builder.annotation_range(name) or error_builder.property_range(name),
                label="missing Windowed[...]",
                raise_error=TypeError,
                code="19",
            )

    cls.__annotations__ = cls_annotations
    del cls_annotations  # unused; set cls.__annotations__ directly

    set_new_attribute(cls=cls, name="__chalk_is_singleton__", value=singleton)
    set_new_attribute(
        cls=cls, name="__chalk_online_store_config__", value=(online_store_config and online_store_config.id)
    )
    set_new_attribute(cls=cls, name="__chalk_error_builder__", value=error_builder)
    set_new_attribute(cls=cls, name="__chalk_source_info__", value=source_info)
    set_new_attribute(cls=cls, name="__chalk_materialized_windows__", value=materialized_windows)
    set_new_attribute(cls=cls, name="__chalk_group_by_materialized_windows__", value=group_by_materialized_windows)
    set_new_attribute(cls=cls, name="__chalk_expression_windows__", value=expression_windows)

    cls_fields: List[Feature] = []

    if singleton:
        if online_store_config is not None:
            error_builder.add_diagnostic(
                message="Singleton feature sets cannot be stored in an online store.",
                label="invalid online store",
                range=error_builder.decorator_kwarg_value_range("online_store_config"),
                raise_error=ValueError,
                code="74",
            )
        f = Feature(
            primary=True,
            attribute_name="__chalk_singleton_id__",
            name="__chalk_singleton_id__",
            default=CHALK_SINGLETON_VALUE,
            namespace=namespace,
            typ=int,
            pyarrow_dtype=pa.uint8(),
            max_staleness=None,
            cache_strategy=CacheStrategy.ALL,
            etl_offline_to_online=False,
            is_autogenerated=True,
            no_display=True,
        )
        f.is_singleton = True
        set_new_attribute(cls=cls, name="__chalk_singleton_id__", value=f)
        cls.__annotations__[f.attribute_name] = int

    def __chalk_primary__(_: Type[Features]):
        return _discover_feature(
            cls_fields,
            "primary",
            lambda q: q._primary is True,
            lambda q: q.typ.is_primary(),
            lambda q: (
                q.name == "id" and not q.has_resolved_join and not q._is_feature_time and not q.typ.is_feature_time()
            ),
        )

    set_new_attribute(cls, "__chalk_primary__", value=classproperty(__chalk_primary__, cached=True))

    def __chalk_ts__(cl: Type[Features]) -> Feature:
        # Not using `f.is_feature_time` as that would create an infinite recursion, since
        # `.is_feature_time` accesses `__chalk_ts__`
        ts_feature: Optional[Feature] = _discover_feature(
            cls_fields,
            "feature time",
            lambda q: q._is_feature_time is True,
            lambda q: q.typ.is_feature_time(),
            lambda q: q.name == "ts" and not q.has_resolved_join and not q._primary and not q.typ.is_primary(),
        )
        if ts_feature is None:
            return unwrap_feature(getattr(cl, GENERATED_OBSERVED_AT_NAME))
        return ts_feature

    set_new_attribute(
        cls=cls,
        name="__chalk_ts__",
        value=classproperty(__chalk_ts__, cached=True),
    )

    def __chalk_observed_at__(cls: Type[Features]) -> FeatureWrapper:
        ts_feature: Optional[Feature] = _discover_feature(
            cls_fields,
            "feature time",
            # Not using `f.is_feature_time` as that would create an infinite recursion, since
            # `.is_feature_time` accesses `__chalk_ts__` which can access this function
            lambda f: f._is_feature_time is True,
            lambda f: f.typ.is_feature_time(),
            lambda f: f.name == "ts" and not f.has_resolved_join and not f._primary and not f.typ.is_primary(),
        )
        if ts_feature is not None:
            if ts_feature.attribute_name != GENERATED_OBSERVED_AT_NAME:
                error_builder.add_diagnostic(
                    message=f"Object {cls.__name__} has no attribute '{GENERATED_OBSERVED_AT_NAME}",
                    label="missing attribute",
                    range=error_builder.property_range(ts_feature.attribute_name),
                    raise_error=AttributeError,
                    code="26",
                )

        # If the timestamp feature is still none, then synthesize one on first use
        ts_feature = feature_time()
        assert ts_feature is not None
        ts_feature.name = GENERATED_OBSERVED_AT_NAME
        ts_feature.attribute_name = GENERATED_OBSERVED_AT_NAME
        ts_feature.unversioned_attribute_name = None
        ts_feature.namespace = cls.__chalk_namespace__
        ts_feature.features_cls = cls
        ts_feature.is_autogenerated = True
        cls.__annotations__[GENERATED_OBSERVED_AT_NAME] = datetime

        _process_field(
            f=ts_feature,
            error_builder=error_builder,
            comments={},
            class_owner=cls.__chalk_owner__,
            class_tags=tuple(cls.__chalk_tags__),
            class_etl_offline_to_online=cls.__chalk_etl_offline_to_online__,
            class_max_staleness=cls.__chalk_max_staleness__,
            class_cache_strategy=cls.__chalk_cache_strategy__,
        )

        return FeatureWrapper(ts_feature)

    set_new_attribute(
        cls=cls,
        name=GENERATED_OBSERVED_AT_NAME,
        value=classproperty(__chalk_observed_at__, cached=True, bind_to_instances=False),
    )

    def __features__(cl: Type[Features]) -> List[Feature]:
        fs = list(cls_fields)
        if cl.__chalk_ts__ not in fs:
            assert cl.__chalk_ts__ is not None
            fs.append(cl.__chalk_ts__)
        return fs

    set_new_attribute(cls=cls, name="features", value=classproperty(__features__, cached=True))
    set_new_attribute(cls=cls, name="__str__", value=classmethod(lambda _: namespace))
    set_new_attribute(cls=cls, name="__chalk_features_raw__", value=cls_fields)
    set_new_attribute(cls=cls, name="__chalk_is_loaded_from_notebook__", value=False)
    set_new_attribute(cls=cls, name="__chalk_notebook_feature_expressions__", value=dict())
    set_new_attribute(cls=cls, name="__repr__", value=_repr_fn)
    set_new_attribute(cls=cls, name="__eq__", value=_eq_fn)
    set_new_attribute(cls=cls, name="__hash__", value=None)
    set_new_attribute(cls=cls, name="__iter__", value=_iter_fn)
    set_new_attribute(cls=cls, name="items", value=_items_fn)
    set_new_attribute(cls=cls, name="namespace", value=namespace)
    set_new_attribute(cls=cls, name="__chalk_namespace__", value=namespace)
    set_new_attribute(cls=cls, name="__chalk_owner__", value=owner)
    set_new_attribute(cls=cls, name="__chalk_tags__", value=list(tags))
    set_new_attribute(cls=cls, name="__chalk_max_staleness__", value=max_staleness)
    set_new_attribute(cls=cls, name="__chalk_cache_strategy__", value=cache_strategy)
    set_new_attribute(cls=cls, name="__is_features__", value=True)
    set_new_attribute(cls=cls, name="__len__", value=_len_fn)
    set_new_attribute(cls=cls, name="__getattribute__", value=_getattribute_fn)
    set_new_attribute(cls=cls, name="__setattr__", value=classmethod(_class_setattr))
    set_new_attribute(
        cls=cls,
        name="__chalk_etl_offline_to_online__",
        value=etl_offline_to_online,
    )


    # Moving this line lower causes all kinds of problems.
    cls = classproperty_support(cls)

    comments = {}
    try:
        # If we pass this function something that isn't a class, it could raise
        comments = _parse_annotation_comments(source_info, cls.__annotations__)
    except:
        pass

    # Parse the fields after we have the correct `cls` set
    cls_fields.extend(
        _get_field(
            cls=cls,
            error_builder=error_builder,
            annotation_name=name,
            comments=comments,
            class_owner=owner,
            class_tags=tags,
            class_etl_offline_to_online=etl_offline_to_online,
            class_max_staleness=max_staleness,
            class_cache_strategy=cache_strategy,
            namespace=namespace,
            is_singleton=singleton,
        )
        for name in cls.__annotations__
    )
    for f in tuple(cls_fields):
        if singleton and f.primary and f.name != "__chalk_singleton_id__":
            error_builder.add_diagnostic(
                message=(
                    f"The singleton feature class '{namespace}' includes a feature '{f.name}' that is primary. "
                    f"Please remove the feature '{f.fqn}' "
                    f"or remove the singleton keyword argument to the feature class '{namespace}'."
                ),
                range=error_builder.property_range(f.attribute_name),
                label="primary feature",
                raise_error=ValueError,
                code="27",
            )

        if f.version is None:
            continue

        alias_from_to[f.attribute_name] = f"{f.attribute_name}_v{f.version.default}"

        if f.version.explicitly_enumerated:
            for i, mapped_feature in f.version.reference.items():
                f_i = copy.copy(mapped_feature)
                f_i.namespace = namespace

                f_i.version = VersionInfo(
                    version=i,
                    maximum=f.version.maximum,
                    default=f.version.default,
                    reference=f.version.reference,
                    base_name=getattr(f_i, "name", None) or f.version.base_name,
                    explicitly_enumerated=False,
                )
                cls_cast = cast(Type, cls)
                if not f_i.is_typ_set():
                    f_i.typ = ParsedAnnotation(cls_cast, f.name)

                f_i.features_cls = cls_cast
                f_i.attribute_name = f"{f.attribute_name}_v{i}"
                if not hasattr(f_i, "name"):
                    f_i.name = f_i.version.name_for_version(i)
                f_i.unversioned_attribute_name = f.attribute_name
                f_i.is_singleton = f.is_singleton
                _process_field(
                    f=f_i,
                    comments=comments,
                    class_owner=owner,
                    class_tags=tags,
                    class_etl_offline_to_online=etl_offline_to_online,
                    class_max_staleness=max_staleness,
                    class_cache_strategy=cache_strategy,
                    error_builder=error_builder,
                )
                f.version.reference[i] = f_i
                # The default feature already exists.
                f_i.no_display = i == f.version.default
            continue

        for i in range(1, f.version.maximum + 1):
            f_i = copy.copy(f)
            f_i.name = f.version.name_for_version(i)
            f_i.unversioned_attribute_name = f.attribute_name
            f_i.attribute_name = f"{f.attribute_name}_v{i}"
            f_i.version = VersionInfo(
                version=i,
                maximum=f.version.maximum,
                default=f.version.default,
                reference=f.version.reference,
                base_name=f.version.base_name,
                explicitly_enumerated=False,
            )
            f.version.reference[i] = f_i
            cls_fields.append(f_i)

            # The default feature already exists.
            f_i.no_display = i == f.version.default

            if f_i.attribute_name in cls.__annotations__:
                assert f_i.features_cls is not None
                error_builder.add_diagnostic(
                    message=(
                        f"The class '{f_i.features_cls.__name__}' "
                        f"has an existing annotation '{f_i.attribute_name}' "
                        "that collides with a versioned feature. Please remove the existing "
                        "annotation, or lower the version."
                    ),
                    range=error_builder.property_range(f_i.attribute_name),
                    label="invalid name",
                    raise_error=ValueError,
                    code="21",
                )
            cls.__annotations__[f_i.attribute_name] = cls.__annotations__[f.attribute_name]

    set_new_attribute(
        cls=cls,
        name="__setattr__",
        value=_setattr_fn(
            bidirectional_alias={**{v: k for k, v in alias_from_to.items()}, **alias_from_to},
        ),
    )

    set_new_attribute(
        cls=cls,
        name="__init__",
        value=_init_fn(
            additional_inits=frozenset(additional_inits),
            alias_from_to=alias_from_to,
        ),
    )

    for f in cls_fields:
        assert f.attribute_name is not None
        f.features_cls = cast(Type[Features], cls)
        # Wrap all class features with FeatureWrapper
        setattr(cls, f.attribute_name, FeatureWrapper(f))

        if f.hook:
            f.hook(cast(Type[Features], cls))

    set_new_attribute(cls=cls, name="__chalk_feature_set__", value=True)
    return cls


def _can_overwrite_feature(cls: Type[Features], key: str, existing_feature: Optional[Feature] = None) -> bool:
    """
    Note: Can't really distinguish between features declared like this in a notebook cell
    vs. features declared like this in code imported from a notebook cell (e.g. customer code)
    Gonna treat both the same since this code only runs in a notebook context
    (e.g. customers can't use this pattern as part of their deployment code)
    """
    from chalk.features.feature_set import FeatureSetBase

    if notebook.is_defined_in_module(cls) and key not in FeatureSetBase.__chalk_notebook_defined_feature_fields__.get(
        cls.namespace, set()
    ):
        if existing_feature is not None:
            return False

    return True


def _class_setattr(
    cls: Type[Features],
    key: str,
    value: Any,
):
    from chalk.features.feature_set import FeatureSetBase

    # Handle inline feature definitions in notebooks
    if (
        (key.startswith("__") and key.endswith("__"))
        or key == "features"
        or key == "namespace"
        or isinstance(value, FeatureWrapper)
    ):
        # If it's a dunder, then  set it directly
        # If it's the literal 'features' or 'namespace', then set it directly -- Chalk reserves these names
        # If it's already a FeatureWrapper, then assume it was already constructed correctly, so set it directly
        type.__setattr__(cls, key, value)
        return
    f = None
    existing_feature = None
    is_notebook_defined_feature = False
    if isinstance(value, Underscore):
        # Handle the case of `User.new_feat: typ = ....` in a notebook
        from chalk.df.ast_parser import parse_inline_setattr_annotation

        fqn = build_namespaced_name(name=f"{cls.namespace}.{key}")
        existing_feature = next((ff for ff in cls.features if ff.fqn == fqn), None)
        typ = parse_inline_setattr_annotation(key)
        is_notebook_defined_feature: bool = notebook.is_notebook()

        if is_notebook_defined_feature and not _can_overwrite_feature(cls, key, existing_feature):
            raise ValueError(
                f"Can't overwrite feature '{cls.namespace}.{key}' because it already exists in the deployment source."
            )

        if typ is None:
            if is_notebook_defined_feature or existing_feature is None:
                raise TypeError(
                    f"Please define a type annotation for feature '{fqn}', like so: User.new_feature: typ = _.a + _.b"
                )
            else:
                parsed_annotation = ParsedAnnotation(underlying=existing_feature.typ.parsed_annotation)
        else:
            parsed_annotation = ParsedAnnotation(underlying=typ)

        # Always create a new feature to avoid type initialization issues
        f = Feature(
            namespace=cls.namespace,
            name=key,
            attribute_name=key,
            features_cls=cls,
            typ=parsed_annotation,
            underscore_expression=value,
        )
    elif isinstance(value, Feature):
        # Handle the case of `User.new_feat = feature(....)` in a notebook
        f = value
        if notebook.is_notebook():
            is_notebook_defined_feature = True
            existing_feature = next((ff for ff in cls.features if ff.unversioned_attribute_name == key), None)
            if not _can_overwrite_feature(cls, key, existing_feature):
                raise ValueError(
                    f"Can't overwrite feature '{cls.namespace}.{key}' because it already exists in the deployment source."
                )
            if hasattr(f, "max_staleness") and f.max_staleness.total_seconds() > 0:
                raise ValueError(
                    "Cannot set `max_staleness` on a notebook defined feature: persistence is not supported for notebook defined features"
                )
            # Get the type annotation
            parsed_annotation: Optional[ParsedAnnotation] = None
            if existing_feature is not None:
                parsed_annotation = ParsedAnnotation(underlying=existing_feature.typ.parsed_annotation)
            if f._typ is not None and f.typ._unparsed_underlying is not None:
                # If the feature already has a type annotation, use that
                parsed_annotation = f.typ
            else:
                from chalk.df.ast_parser import parse_inline_setattr_annotation

                typ = parse_inline_setattr_annotation(key)
                if typ is not None:
                    parsed_annotation = ParsedAnnotation(underlying=typ)
            if parsed_annotation is None:
                raise TypeError(
                    f"Please define a type annotation for feature '{cls.namespace}.{key}', like so: User.new_feature=feature(typ=str)"
                )
            # Set some attributes that usually get set when the feature is created inside the class definition
            f.attribute_name = key
            f.unversioned_attribute_name = key
            if getattr(f, "name", None) is None:
                f.name = key
            f.namespace = cls.namespace
            f.typ = parsed_annotation
    else:
        # Passing a feature in directly is used internally, so not mentioning that in the error message
        raise TypeError(
            (
                f"In order to define feature '{cls.namespace}.{key}', "
                "please set it equal to an underscore expression. "
                f"For example, `{cls.__name__}.{key}: int = _.a + _.b`."
            )
        )

    # Clear the cache so that the new feature definition propagates
    Feature._from_root_fqn.cache_clear()

    # Process feature field
    f.features_cls = cls
    _process_field(
        f=f,
        error_builder=cls.__chalk_error_builder__,
        comments={},
        class_owner=cls.__chalk_owner__,
        class_tags=tuple(cls.__chalk_tags__),
        class_etl_offline_to_online=cls.__chalk_etl_offline_to_online__,
        class_max_staleness=cls.__chalk_max_staleness__,
        class_cache_strategy=cls.__chalk_cache_strategy__,
    )
    if existing_feature is not None:
        cls.features.remove(existing_feature)
    cls.features.append(f)
    wrapped_feature = FeatureWrapper(f)
    type.__setattr__(cls, key, wrapped_feature)
    if is_notebook_defined_feature:
        assert f.unversioned_attribute_name is not None  # for pyright
        FeatureSetBase.__chalk_notebook_defined_feature_fields__[cls.namespace].add(f.unversioned_attribute_name)


def parse_quoted_window_feature(annotation_str: str, module_str: str) -> Type[Windowed]:
    """
    Parses a string like "Windowed[int]", "Windowed[list[int]]", "Windowed[SomeStruct]"
    and returns Windowed with the appropriate type.
    """
    match = re.fullmatch(r"Windowed\[(.+)\]", annotation_str)
    if not match:
        raise ValueError(f"Invalid type format: {annotation_str}")

    inner_type_str = match.group(1)

    try:
        # Handle built-in types and typing constructs
        inner_type = eval(inner_type_str, {"__builtins__": builtins, **typing.__dict__})
    except NameError:
        # If it's not a built-in type, assume it's a user-defined type
        try:
            module = sys.modules.get(module_str, None)
            inner_type = getattr(module, "__dict__", {})[inner_type_str]
        except KeyError:
            raise ValueError(f"Unknown type: {inner_type_str}")

    return Windowed[inner_type]
