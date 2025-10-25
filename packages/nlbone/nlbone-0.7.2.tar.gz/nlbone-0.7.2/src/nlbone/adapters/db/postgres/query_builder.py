from typing import Any, Callable, Optional, Sequence, Type, Union

from sqlalchemy import and_, asc, case, desc, literal, or_
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Query, Session, aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.interfaces import LoaderOption
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.sqltypes import (
    BigInteger,
    Boolean,
    Float,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.sql.sqltypes import (
    Enum as SAEnum,
)

from nlbone.interfaces.api.exceptions import UnprocessableEntityException
from nlbone.interfaces.api.pagination import PaginateRequest, PaginateResponse

NULL_SENTINELS = ("None", "null", "")


class _InvalidEnum(Exception):
    pass


def _resolve_column_and_joins(entity, query, field_path: str, join_cache: dict[str, Any]):
    parts = [p for p in field_path.split(".") if p]
    if not parts:
        return None, query

    current_cls_or_alias = entity
    current_path_key_parts: list[str] = []

    for i, part in enumerate(parts):
        current_path_key_parts.append(part)
        path_key = ".".join(current_path_key_parts)

        if not hasattr(current_cls_or_alias, part):
            return None, query

        attr = getattr(current_cls_or_alias, part)

        prop = getattr(attr, "property", None)
        if isinstance(prop, RelationshipProperty):
            alias = join_cache.get(path_key)
            if alias is None:
                alias = aliased(prop.mapper.class_)
                query = query.outerjoin(alias, attr)
                join_cache[path_key] = alias
            current_cls_or_alias = alias
            continue

        if isinstance(attr, InstrumentedAttribute):
            if i == len(parts) - 1:
                return attr, query
            else:
                return None, query

        return None, query

    return None, query


def _apply_order(pagination: PaginateRequest, entity, query):
    order_clauses = []

    include_ids = getattr(pagination, "include_ids", []) or []
    if include_ids and hasattr(entity, "id"):
        id_col = getattr(entity, "id")
        whens = [(id_col == _id, idx) for idx, _id in enumerate(include_ids)]
        order_clauses.append(asc(case(*whens, else_=literal(999_999))))

    if pagination.sort:
        for sort in pagination.sort:
            field = sort["field"]
            order = sort["order"]

            if hasattr(entity, field):
                column = getattr(entity, field)
                if order == "asc":
                    order_clauses.append(asc(column))
                else:
                    order_clauses.append(desc(column))

    if order_clauses:
        query = query.order_by(*order_clauses)
    return query


def _coerce_enum(col_type, raw):
    if raw is None:
        return None
    enum_cls = getattr(col_type, "enum_class", None)
    if enum_cls is not None:
        if isinstance(raw, enum_cls):
            return raw
        if isinstance(raw, str):
            low = raw.strip().lower()
            for m in enum_cls:
                if m.name.lower() == low or str(m.value).lower() == low:
                    return m
        raise _InvalidEnum(f"'{raw}' is not one of {[m.name for m in enum_cls]}")
    choices = list(getattr(col_type, "enums", []) or [])
    if isinstance(raw, str):
        low = raw.strip().lower()
        for c in choices:
            if c.lower() == low:
                return c
    raise _InvalidEnum(f"'{raw}' is not one of {choices or '[no choices defined]'}")


def _is_text_type(coltype):
    return isinstance(coltype, (String, Text))


def _looks_like_wildcard(s: str) -> bool:
    # treat '*' and '%' as wildcards
    return isinstance(s, str) and ("*" in s or "%" in s)


def _to_sql_like_pattern(s: str) -> str:
    if s is None:
        return None
    s = str(s)
    s = s.replace("*", "%")
    if "%" not in s:
        s = f"%{s}%"
    return s


def _parse_field_and_op(field: str):
    """
    Supports suffix operators like:
      __ilike, __gte, __lte, __lt, __gt, __ne
    Returns (base_field, op) where op in {'eq','ilike','gte','lte','lt','gt','ne'}
    """
    if "__" in field:
        base, op = field.rsplit("__", 1)
        op = op.lower()
        if base and op in {"ilike", "gte", "lte", "lt", "gt", "ne"}:
            return base, op
    return field, "eq"


def _apply_filters(pagination, entity, query):
    if not getattr(pagination, "filters", None) and not getattr(pagination, "include_ids", None):
        return query

    predicates = []
    join_cache: dict[str, Any] = {}

    if getattr(pagination, "filters", None):
        for raw_field, value in pagination.filters.items():
            if value is None or value in NULL_SENTINELS or value == [] or value == {}:
                value = None

            field, op_hint = _parse_field_and_op(raw_field)

            col, query2 = _resolve_column_and_joins(entity, query, field, join_cache)
            if col is None:
                continue
            query = query2
            coltype = getattr(col, "type", None)

            def coerce(v):
                if v is None:
                    return None
                # Enums
                if isinstance(coltype, (SAEnum, PGEnum)):
                    return _coerce_enum(coltype, v)
                # Text
                if _is_text_type(coltype):
                    return str(v)
                # Numbers
                if isinstance(coltype, (Integer, BigInteger, SmallInteger)):
                    return int(v)
                if isinstance(coltype, (Float, Numeric)):
                    return float(v)
                # Booleans
                if isinstance(coltype, Boolean):
                    if isinstance(v, bool):
                        return v
                    if isinstance(v, (int, float)):
                        return bool(v)
                    if isinstance(v, str):
                        vl = v.strip().lower()
                        if vl in {"true", "1", "yes", "y", "t"}:
                            return True
                        if vl in {"false", "0", "no", "n", "f"}:
                            return False
                    return None
                return v

            try:

                def _use_ilike(v) -> bool:
                    if op_hint == "ilike":
                        return True
                    if _is_text_type(coltype) and isinstance(v, str) and _looks_like_wildcard(v):
                        return True
                    return False

                if isinstance(value, (list, tuple, set)):
                    vals = [v for v in value if v not in (None, "", "null", "None")]
                    if not vals:
                        continue

                    if any(_use_ilike(v) for v in vals) and _is_text_type(coltype):
                        patterns = [_to_sql_like_pattern(str(v)) for v in vals]
                        predicates.append(or_(*[col.ilike(p) for p in patterns]))
                    else:
                        coerced = [coerce(v) for v in vals if v is not None]
                        if not coerced:
                            continue

                        if op_hint == "eq":
                            predicates.append(col.in_(coerced))
                        elif op_hint == "ne":
                            predicates.append(or_(*[col != v for v in coerced]))
                        elif op_hint == "gt":
                            predicates.append(or_(*[col > v for v in coerced]))
                        elif op_hint == "gte":
                            predicates.append(or_(*[col >= v for v in coerced]))
                        elif op_hint == "lt":
                            predicates.append(or_(*[col < v for v in coerced]))
                        elif op_hint == "lte":
                            predicates.append(or_(*[col <= v for v in coerced]))
                        else:
                            predicates.append(col.in_(coerced))
                else:
                    if _use_ilike(value) and _is_text_type(coltype):
                        pattern = _to_sql_like_pattern(str(value))
                        predicates.append(col.ilike(pattern))
                    else:
                        v = coerce(value)
                        if v is None:
                            if op_hint in {"eq", "ilike"}:
                                predicates.append(col.is_(None))
                            else:
                                continue
                        else:
                            if op_hint == "eq":
                                predicates.append(col == v)
                            elif op_hint == "ne":
                                predicates.append(col != v)
                            elif op_hint == "gt":
                                predicates.append(col > v)
                            elif op_hint == "gte":
                                predicates.append(col >= v)
                            elif op_hint == "lt":
                                predicates.append(col < v)
                            elif op_hint == "lte":
                                predicates.append(col <= v)
                            else:
                                predicates.append(col == v)

            except _InvalidEnum as e:
                raise UnprocessableEntityException(str(e), loc=["query", "filters", raw_field]) from e

    include_ids = getattr(pagination, "include_ids", []) or []
    if include_ids and hasattr(entity, "id"):
        id_col = getattr(entity, "id")
        include_pred = id_col.in_(include_ids)
        if predicates:
            final_pred = or_(and_(*predicates), include_pred)
        else:
            final_pred = or_(and_(*[1 == 1]), include_pred)
        return query.filter(final_pred)

    if predicates:
        query = query.filter(and_(*predicates))
    return query


def apply_pagination(pagination: PaginateRequest, entity, session: Session, limit=True, query=None) -> Query:
    if not query:
        query = session.query(entity)
    query = _apply_filters(pagination, entity, query)
    query = _apply_order(pagination, entity, query)
    if limit:
        query = query.limit(pagination.limit).offset(pagination.offset)
    return query


OutputType = Union[type, Callable[[Any], Any], None]


def _serialize_item(item: Any, output_cls: OutputType) -> Any:
    """Serialize a single ORM item based on output_cls (Pydantic v1/v2 or custom mapper)."""
    if output_cls is None:
        return item

    if callable(output_cls) and not isinstance(output_cls, type):
        return output_cls(item)

    if hasattr(output_cls, "model_validate"):
        try:
            model = output_cls.model_validate(item, from_attributes=True)
            if hasattr(model, "model_dump"):
                return model.model_dump()
            return model
        except Exception:
            pass

    if hasattr(output_cls, "from_orm"):
        try:
            model = output_cls.from_orm(item)
            if hasattr(model, "dict"):
                return model.dict()
            return model
        except Exception:
            pass

    try:
        obj = output_cls(item)
        try:
            from dataclasses import asdict, is_dataclass

            if is_dataclass(obj):
                return asdict(obj)
        except Exception:
            pass
        return obj
    except Exception:
        return item


def get_paginated_response(
    pagination,
    entity,
    session: Session,
    *,
    with_count: bool = True,
    output_cls: Optional[Type] = None,
    eager_options: Optional[Sequence[LoaderOption]] = None,
    query=None,
) -> dict:
    if not query:
        query = session.query(entity)
    if eager_options:
        query = query.options(*eager_options)

    query = apply_pagination(pagination, entity, session, not with_count, query=query)

    total_count = None
    if with_count:
        total_count = query.count()
        query = query.limit(pagination.limit).offset(pagination.offset)

    rows = query.all()

    if output_cls is not None:
        data = [output_cls.model_validate(r, from_attributes=True).model_dump() for r in rows]
    else:
        data = rows
    return PaginateResponse(
        total_count=total_count, data=data, limit=pagination.limit, offset=pagination.offset
    ).to_dict()
