"""Used to convert JAQueL queries to ASAM ODS SelectStatements"""

from __future__ import annotations

import json
import re
from datetime import datetime
from difflib import get_close_matches
from typing import Any

from google.protobuf.internal import containers as _containers

import odsbox.proto.ods_pb2 as ods
from odsbox.jaquel_conversion_result import JaquelConversionResult

OperatorEnum = ods.SelectStatement.ConditionItem.Condition.OperatorEnum


_jo_aggregates = {
    "$none": ods.AggregateEnum.AG_NONE,
    "$count": ods.AggregateEnum.AG_COUNT,
    "$dcount": ods.AggregateEnum.AG_DCOUNT,
    "$min": ods.AggregateEnum.AG_MIN,
    "$max": ods.AggregateEnum.AG_MAX,
    "$avg": ods.AggregateEnum.AG_AVG,
    "$stddev": ods.AggregateEnum.AG_STDDEV,
    "$sum": ods.AggregateEnum.AG_SUM,
    "$distinct": ods.AggregateEnum.AG_DISTINCT,
    "$point": ods.AggregateEnum.AG_VALUES_POINT,
    "$ia": ods.AggregateEnum.AG_INSTANCE_ATTRIBUTE,
}
_jo_operators = {
    "$eq": OperatorEnum.OP_EQ,
    "$neq": OperatorEnum.OP_NEQ,
    "$lt": OperatorEnum.OP_LT,
    "$gt": OperatorEnum.OP_GT,
    "$lte": OperatorEnum.OP_LTE,
    "$gte": OperatorEnum.OP_GTE,
    "$in": OperatorEnum.OP_INSET,
    "$notinset": OperatorEnum.OP_NOTINSET,
    "$like": OperatorEnum.OP_LIKE,
    "$null": OperatorEnum.OP_IS_NULL,
    "$notnull": OperatorEnum.OP_IS_NOT_NULL,
    "$notlike": OperatorEnum.OP_NOTLIKE,
    "$between": OperatorEnum.OP_BETWEEN,
}
_jo_operators_ci_map = {
    OperatorEnum.OP_EQ: OperatorEnum.OP_CI_EQ,
    OperatorEnum.OP_NEQ: OperatorEnum.OP_CI_NEQ,
    OperatorEnum.OP_LT: OperatorEnum.OP_CI_LT,
    OperatorEnum.OP_GT: OperatorEnum.OP_CI_GT,
    OperatorEnum.OP_LTE: OperatorEnum.OP_CI_LTE,
    OperatorEnum.OP_GTE: OperatorEnum.OP_CI_GTE,
    OperatorEnum.OP_INSET: OperatorEnum.OP_CI_INSET,
    OperatorEnum.OP_NOTINSET: OperatorEnum.OP_CI_NOTINSET,
    OperatorEnum.OP_LIKE: OperatorEnum.OP_CI_LIKE,
    OperatorEnum.OP_NOTLIKE: OperatorEnum.OP_CI_NOTLIKE,
}


def _result_column_path(path: str, aggregate: ods.AggregateEnum) -> str:
    if aggregate is None or aggregate == ods.AggregateEnum.AG_NONE:
        return path

    for jaquel_name, enum_value in _jo_aggregates.items():
        if enum_value == aggregate:
            return f"{path}.{jaquel_name}"

    return path


def _model_get_relation_by_base_name(
    model: ods.Model, entity: ods.Model.Entity, relation_base_name: str
) -> ods.Model.Relation | None:
    for rel in entity.relations:
        if entity.relations[rel].base_name.lower() == relation_base_name.lower():
            return entity.relations[rel]
    return None


def _model_get_relation_by_application_name(
    model: ods.Model, entity: ods.Model.Entity, relation_application_name: str
) -> ods.Model.Relation | None:
    for rel in entity.relations:
        if entity.relations[rel].name.lower() == relation_application_name.lower():
            return entity.relations[rel]
    return None


def _model_get_relation(model: ods.Model, entity: ods.Model.Entity, relation_name: str) -> ods.Model.Relation | None:
    rv = _model_get_relation_by_application_name(model, entity, relation_name)
    if rv is None:
        rv = _model_get_relation_by_base_name(model, entity, relation_name)
    if rv is not None:
        return rv

    return None


def _model_get_attribute_by_base_name(
    model: ods.Model, entity: ods.Model.Entity, attribute_base_name: str
) -> ods.Model.Attribute | None:
    for attr in entity.attributes:
        if entity.attributes[attr].base_name.lower() == attribute_base_name.lower():
            return entity.attributes[attr]
    return None


def _model_get_attribute_by_application_name(
    model: ods.Model, entity: ods.Model.Entity, attribute_name: str
) -> ods.Model.Attribute | None:
    for attr in entity.attributes:
        if entity.attributes[attr].name.lower() == attribute_name.lower():
            return entity.attributes[attr]
    return None


def _model_get_attribute(model: ods.Model, entity: ods.Model.Entity, attribute_name: str) -> ods.Model.Attribute | None:
    rv = _model_get_attribute_by_application_name(model, entity, attribute_name)
    if rv is None:
        rv = _model_get_attribute_by_base_name(model, entity, attribute_name)
    if rv is not None:
        return rv

    return None


def _model_get_entity_ex(model: ods.Model, entity_name_or_aid: str | int) -> ods.Model.Entity:
    if isinstance(entity_name_or_aid, int) or entity_name_or_aid.isdigit():
        entity_aid = int(entity_name_or_aid)
        for key in model.entities:
            entity = model.entities[key]
            if entity.aid == entity_aid:
                return entity
        raise SyntaxError(f"'{entity_aid}' is not a valid entity aid.")

    for key in model.entities:
        entity = model.entities[key]
        if entity.name.lower() == entity_name_or_aid.lower() or entity.base_name.lower() == entity_name_or_aid.lower():
            return entity

    raise SyntaxError(
        f"Entity '{entity_name_or_aid}' is unknown in model.{_model_get_suggestion_entity(model, entity_name_or_aid)}"
    )


def _model_get_suggestion(lower_case_dict: dict, str_val: str) -> str:
    suggestions = get_close_matches(
        str_val.lower(),
        lower_case_dict,
        n=1,
        cutoff=0.3,
    )
    if len(suggestions) > 0:
        return_value = lower_case_dict[suggestions[0]]
        return f" Did you mean '{return_value}'?"
    return ""


def _model_get_enum_suggestion(enumeration: ods.Model.Enumeration, str_val: str) -> str:
    available = {key.lower(): key for key in enumeration.items}
    return _model_get_suggestion(available, str_val)


def _model_get_suggestion_attribute(entity: ods.Model.Entity, attribute_or_relation_name: str) -> str:
    available = {}
    available.update({relation.base_name.lower(): relation.base_name for key, relation in entity.relations.items()})
    available.update({attribute.base_name.lower(): attribute.base_name for key, attribute in entity.attributes.items()})
    available.update({relation.name.lower(): relation.name for key, relation in entity.relations.items()})
    available.update({attribute.name.lower(): attribute.name for key, attribute in entity.attributes.items()})
    return _model_get_suggestion(available, attribute_or_relation_name)


def _model_get_suggestion_relation(entity: ods.Model.Entity, relation_name: str) -> str:
    available = {}
    available.update({relation.base_name.lower(): relation.base_name for key, relation in entity.relations.items()})
    available.update({relation.name.lower(): relation.name for key, relation in entity.relations.items()})
    return _model_get_suggestion(available, relation_name)


def _model_get_suggestion_entity(model: ods.Model, entity_name: str) -> str:
    available = {}
    available.update({entity.base_name.lower(): entity.base_name for key, entity in model.entities.items()})
    available.update({entity.name.lower(): entity.name for key, entity in model.entities.items()})
    return _model_get_suggestion(available, entity_name)


def _model_get_suggestion_aggregate(aggregate_name: str) -> str:
    available = {key.lower(): key for key in _jo_aggregates}
    available["$nested"] = "$nested"
    return _model_get_suggestion(available, aggregate_name)


def _model_get_suggestion_operators(operator_name: str) -> str:
    available = {key.lower(): key for key in _jo_operators}
    return _model_get_suggestion(available, operator_name)


def _model_get_enum_index(model: ods.Model, entity: ods.Model.Entity, attribute_name: str, str_val: str) -> int:
    attr = entity.attributes[attribute_name]
    enum = model.enumerations[attr.enumeration]
    for key in enum.items:
        if key.lower() == str_val.lower():
            return enum.items[key]

    raise SyntaxError(f"Enum entry for '{str_val}' does not exist.{_model_get_enum_suggestion(enum, str_val)}")


def _jo_enum_get_numeric_value(
    model: ods.Model,
    attribute_entity: ods.Model.Entity,
    attribute_name: str,
    name_or_number: str | int,
) -> int:
    if isinstance(name_or_number, str):
        return int(_model_get_enum_index(model, attribute_entity, attribute_name, name_or_number))

    return int(name_or_number)


def _jo_date(date_value: str | datetime) -> str:
    tv = None
    if isinstance(date_value, str):
        if "T" in date_value:
            format_string = "%Y-%m-%dT%H:%M:%S"
            if "." in date_value:
                format_string += ".%f"
            if date_value.endswith("Z"):
                format_string += "Z"
            tv = datetime.strptime(date_value, format_string)
        else:
            return date_value
    else:
        tv = date_value
    return re.sub(r"(?<=[^\s]{14})0+$", "", tv.strftime("%Y%m%d%H%M%S%f"))


def _parse_path_and_add_joins(
    model: ods.Model,
    entity: ods.Model.Entity,
    attribute_path: str,
    joins: _containers.RepeatedCompositeFieldContainer[ods.SelectStatement.JoinItem],
) -> tuple[ods.DataTypeEnum, str, ods.Model.Entity]:
    attribute_type = ods.DataTypeEnum.DT_UNKNOWN
    attribute_name = ""
    attribute_entity = entity
    path_parts = attribute_path.split(".")
    path_part_length = len(path_parts)
    for i in range(path_part_length):
        path_part = path_parts[i]
        join_type = ods.SelectStatement.JoinItem.JoinTypeEnum.JT_DEFAULT
        if path_part.endswith(":OUTER"):
            path_part = path_part[:-6]
            join_type = ods.SelectStatement.JoinItem.JoinTypeEnum.JT_OUTER

        if i != path_part_length - 1:
            # Must be a relation
            relation = _model_get_relation(model, attribute_entity, path_part)
            if relation is None:
                suggestion_text = _model_get_suggestion_relation(attribute_entity, path_part)
                raise SyntaxError(f"'{path_part}' is no relation of entity '{attribute_entity.name}'.{suggestion_text}")
            attribute_name = relation.name

            # add join
            if (
                (-1 == relation.range_max)
                and (1 == relation.inverse_range_max)
                and join_type != ods.SelectStatement.JoinItem.JoinTypeEnum.JT_OUTER
            ):
                # in case of OUTER join the direction is important and must be like addressed
                inverse_entity = model.entities[relation.entity_name]
                inverse_relation = inverse_entity.relations[relation.inverse_name]
                _add_join_to_seq(model, inverse_entity, inverse_relation, joins, join_type)
            else:
                _add_join_to_seq(model, attribute_entity, relation, joins, join_type)

            attribute_entity = model.entities[relation.entity_name]
        else:
            if "*" == path_part:
                attribute_name = "*"
                attribute_type = ods.DataTypeEnum.DT_UNKNOWN
            else:
                # maybe relation or attribute
                attribute = _model_get_attribute(model, attribute_entity, path_part)
                if attribute is not None:
                    attribute_name = attribute.name
                    attribute_type = attribute.data_type
                else:
                    relation = _model_get_relation(model, attribute_entity, path_part)
                    if relation is None:
                        suggestion_text = _model_get_suggestion_attribute(attribute_entity, path_part)
                        raise SyntaxError(
                            f"'{path_part}' is neither attribute nor relation of entity '{attribute_entity.name}'.{suggestion_text}"  # noqa: E501
                        )
                    attribute_name = relation.name
                    attribute_type = ods.DataTypeEnum.DT_LONGLONG  # its an id
    return attribute_type, attribute_name, attribute_entity


def _add_join_to_seq(
    model: ods.Model,
    entity_from: ods.Model.Entity,
    relation: ods.Model.Relation,
    join_sequence: _containers.RepeatedCompositeFieldContainer[ods.SelectStatement.JoinItem],
    join_type: ods.SelectStatement.JoinItem.JoinTypeEnum,
) -> None:
    entity_to = model.entities[relation.entity_name]
    for join in join_sequence:
        if join.aid_from == entity_from.aid and join.aid_to == entity_to.aid and join.relation == relation.name:
            # already in sequence
            return

    join_sequence.add(
        aid_from=entity_from.aid,
        aid_to=entity_to.aid,
        relation=relation.name,
        join_type=join_type,
    )


def _suggestion_for_options(option_name: str) -> str:
    available = {key.lower(): key for key in ["$rowlimit", "$rowskip", "$seqlimit", "$seqskip"]}
    return _model_get_suggestion(available, option_name)


def _parse_global_options(elem_dict: dict, target: ods.SelectStatement) -> None:
    for elem in elem_dict:
        if elem.startswith("$"):
            if "$rowlimit" == elem:
                target.row_limit = int(elem_dict[elem])
            elif "$rowskip" == elem:
                target.row_start = int(elem_dict[elem])
            elif "$seqlimit" == elem:
                target.values_limit = int(elem_dict[elem])
            elif "$seqskip" == elem:
                target.values_start = int(elem_dict[elem])
            else:
                raise SyntaxError(f"Unknown option '{elem}'.{_suggestion_for_options(elem)}")
        else:
            raise SyntaxError(f"No undefined options allowed '{elem}'.{_suggestion_for_options(elem)}")


def _parse_attributes(
    model: ods.Model,
    entity: ods.Model.Entity,
    select_statement: ods.SelectStatement,
    element_dict: dict,
    attribute_dict: dict,
    result_column_lookup: list[JaquelConversionResult.Column],
) -> None:
    for element in element_dict:
        element_attribute = attribute_dict.copy()

        if element.startswith("$"):
            if element in _jo_aggregates:
                element_attribute["aggregate"] = _jo_aggregates[element]
            elif "$unit" == element:
                element_attribute["unit"] = element_dict[element]
                continue
            elif "$options" == element:
                raise SyntaxError("No $options are defined for attributes.")
            else:
                raise SyntaxError(f"Unknown aggregate '{element}'.{_model_get_suggestion_aggregate(element)}")
        else:
            if element_attribute["path"]:
                element_attribute["path"] += "."
            element_attribute["path"] += element

        if isinstance(element_dict[element], dict):
            _parse_attributes(
                model, entity, select_statement, element_dict[element], element_attribute, result_column_lookup
            )
        elif isinstance(element_dict[element], list):
            raise SyntaxError("Attributes are not allowed to contain arrays. Use dictionary setting value to 1.")
        else:
            attribute_path = element_attribute["path"]
            attribute_aggregate = element_attribute["aggregate"]
            _attribute_type, attribute_name, attribute_entity = _parse_path_and_add_joins(
                model, entity, attribute_path, select_statement.joins
            )

            if "*" == attribute_name:
                select_statement.columns.add(aid=attribute_entity.aid, attribute=attribute_name)
            else:
                select_statement.columns.add(
                    aid=attribute_entity.aid,
                    attribute=attribute_name,
                    unit_id=int(element_attribute["unit"]),
                    aggregate=attribute_aggregate,
                )

            result_column_lookup.append(
                JaquelConversionResult.Column(
                    aid=attribute_entity.aid,
                    name=attribute_name,
                    aggregate=attribute_aggregate,
                    path=_result_column_path(attribute_path, attribute_aggregate),
                )
            )


def _parse_orderby(
    model: ods.Model,
    entity: ods.Model.Entity,
    target: ods.SelectStatement,
    element_dict: dict,
    attribute_dict: dict,
) -> None:
    for elem in element_dict:
        if elem.startswith("$"):
            raise SyntaxError(f"No predefined element '{elem}' defined in orderby.")
        elem_attribute = attribute_dict.copy()
        if elem_attribute["path"]:
            elem_attribute["path"] += "."
        elem_attribute["path"] += elem

        if isinstance(element_dict[elem], dict):
            _parse_orderby(model, entity, target, element_dict[elem], elem_attribute)
        elif isinstance(element_dict[elem], list):
            raise SyntaxError("Attributes are not allowed to contain arrays. Use dictionary setting value to 1.")
        else:
            _attribute_type, attribute_name, attribute_entity = _parse_path_and_add_joins(
                model, entity, elem_attribute["path"], target.joins
            )
            order = ods.SelectStatement.OrderByItem.OD_ASCENDING
            if 0 == element_dict[elem]:
                order = ods.SelectStatement.OrderByItem.OD_DESCENDING
            elif 1 == element_dict[elem]:
                order = ods.SelectStatement.OrderByItem.OD_ASCENDING
            else:
                raise SyntaxError(f"'{element_dict[elem]}' is not supported for orderby.")
            target.order_by.add(aid=attribute_entity.aid, attribute=attribute_name, order=order)


def _parse_groupby(
    model: ods.Model,
    entity: ods.Model.Entity,
    target: ods.SelectStatement,
    element_dict: dict,
    attribute_dict: dict,
) -> None:
    for elem in element_dict:
        if elem.startswith("$"):
            raise SyntaxError(f"No predefined element '{elem}' defined in orderby.")
        elem_attribute = attribute_dict.copy()
        if elem_attribute["path"]:
            elem_attribute["path"] += "."
        elem_attribute["path"] += elem
        if isinstance(element_dict[elem], dict):
            _parse_groupby(model, entity, target, element_dict[elem], elem_attribute)
        elif isinstance(element_dict[elem], list):
            raise SyntaxError("Attributes are not allowed to contain arrays. Use dictionary setting value to 1.")
        else:
            if 1 != element_dict[elem]:
                raise SyntaxError(f"Only 1 is supported in groupby, but '{element_dict[elem]}' was provided.")
            _attribute_type, attribute_name, attribute_entity = _parse_path_and_add_joins(
                model, entity, elem_attribute["path"], target.joins
            )
            target.group_by.add(aid=attribute_entity.aid, attribute=attribute_name)


def _parse_conditions_conjunction(
    model: ods.Model,
    entity: ods.Model.Entity,
    conjunction: ods.SelectStatement.ConditionItem.ConjuctionEnum,
    target: ods.SelectStatement,
    element_list: list,
    attribute_dict: dict,
) -> None:
    if not isinstance(element_list, list):
        raise SyntaxError("$and and $or must always contain an array.")

    if attribute_dict["conjunction_count"] > 0:
        target.where.add().conjunction = attribute_dict["conjunction"]

    if len(element_list) > 1:
        target.where.add().conjunction = ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_OPEN

    first_time = True
    for elem in element_list:
        if not isinstance(elem, dict):
            raise SyntaxError("$and and $or arrays must always contain dictionaries.")

        if not first_time:
            target.where.add().conjunction = conjunction

        target.where.add().conjunction = ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_OPEN
        elem_attribute = attribute_dict.copy()
        elem_attribute["conjunction_count"] = 0
        elem_attribute["conjunction"] = ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_AND
        elem_attribute["options"] = ""
        _parse_conditions(model, entity, target, elem, elem_attribute)
        target.where.add().conjunction = ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_CLOSE
        first_time = False

    if len(element_list) > 1:
        target.where.add().conjunction = ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_CLOSE


def _parse_conditions_not(
    model: ods.Model,
    entity: ods.Model.Entity,
    target: ods.SelectStatement,
    element_dict: dict,
    attribute_dict: dict,
) -> None:
    if not isinstance(element_dict, dict):
        raise SyntaxError("$not must always contain a dictionary.")

    if attribute_dict["conjunction_count"] > 0:
        target.where.add().conjunction = attribute_dict["conjunction"]

    elem_attribute = attribute_dict.copy()
    elem_attribute["conjunction_count"] = 0
    elem_attribute["conjunction"] = ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_AND
    elem_attribute["options"] = ""

    target.where.add().conjunction = ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_NOT
    target.where.add().conjunction = ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_OPEN
    _parse_conditions(model, entity, target, element_dict, elem_attribute)
    target.where.add().conjunction = ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_CLOSE


def _handle_nested_statement(
    model: ods.Model,
    entity: ods.Model.Entity,
    target: ods.SelectStatement,
    condition_path: str,
    nested_query_dict: dict,
    condition_unit_id: int,
    condition_options: str,
    condition_operator: OperatorEnum = OperatorEnum.OP_INSET,
) -> None:
    """
    Handle $nested operator by creating a nested SelectStatement.

    :param ods.Model model: application model to be used for conversion.
    :param ods.Model.Entity entity: current entity context
    :param ods.SelectStatement target: target SelectStatement to add condition to
    :param str condition_path: path to the attribute
    :param dict nested_query_dict: nested jaquel query dictionary
    :param int condition_unit_id: unit id for the condition
    :param str condition_options: condition options
    :param OperatorEnum condition_operator: operator to use with the nested statement
    """
    # Create nested SelectStatement from the nested query
    nested_entity, nested_statement = jaquel_to_ods(model, nested_query_dict)

    # Get attribute information for the condition
    attribute_type, attribute_name, attribute_entity = _parse_path_and_add_joins(
        model, entity, condition_path, target.joins
    )

    # Create condition item with nested statement
    condition_item = target.where.add()
    condition_item.condition.aid = attribute_entity.aid
    condition_item.condition.attribute = attribute_name
    condition_item.condition.operator = _get_ods_operator(attribute_type, condition_operator, condition_options)
    condition_item.condition.unit_id = int(condition_unit_id)
    condition_item.condition.nested_statement.CopyFrom(nested_statement)


def _set_condition_value(
    model: ods.Model,
    attribute_entity: ods.Model.Entity,
    attribute_name: str,
    attribute_type: ods.DataTypeEnum,
    src_values: list[Any] | Any,
    condition_item: ods.SelectStatement.ConditionItem.Condition,
) -> None:
    if isinstance(src_values, list):
        if attribute_type in (ods.DataTypeEnum.DT_BYTE, ods.DataTypeEnum.DS_BYTE):
            byte_values = []
            for src_value in src_values:
                byte_values.append(int(src_value))
            condition_item.byte_array.values = bytes(byte_values)
        elif attribute_type in (
            ods.DataTypeEnum.DT_BOOLEAN,
            ods.DataTypeEnum.DS_BOOLEAN,
        ):
            for src_value in src_values:
                condition_item.boolean_array.values.append(bool(src_value))
        elif attribute_type in (ods.DataTypeEnum.DT_SHORT, ods.DataTypeEnum.DS_SHORT):
            for src_value in src_values:
                condition_item.long_array.values.append(int(src_value))
        elif attribute_type in (ods.DataTypeEnum.DT_LONG, ods.DataTypeEnum.DS_LONG):
            for src_value in src_values:
                condition_item.long_array.values.append(int(src_value))
        elif attribute_type in (
            ods.DataTypeEnum.DT_LONGLONG,
            ods.DataTypeEnum.DS_LONGLONG,
        ):
            for src_value in src_values:
                condition_item.longlong_array.values.append(int(src_value))
        elif attribute_type in (ods.DataTypeEnum.DT_FLOAT, ods.DataTypeEnum.DS_FLOAT):
            for src_value in src_values:
                condition_item.float_array.values.append(float(src_value))
        elif attribute_type in (ods.DataTypeEnum.DT_DOUBLE, ods.DataTypeEnum.DS_DOUBLE):
            for src_value in src_values:
                condition_item.double_array.values.append(float(src_value))
        elif attribute_type in (ods.DataTypeEnum.DT_DATE, ods.DataTypeEnum.DS_DATE):
            for src_value in src_values:
                condition_item.string_array.values.append(_jo_date(src_value))
        elif attribute_type in (ods.DataTypeEnum.DT_STRING, ods.DataTypeEnum.DS_STRING):
            for src_value in src_values:
                condition_item.string_array.values.append(str(src_value))
        elif attribute_type in (ods.DataTypeEnum.DT_ENUM, ods.DataTypeEnum.DS_ENUM):
            for src_value in src_values:
                condition_item.long_array.values.append(
                    _jo_enum_get_numeric_value(model, attribute_entity, attribute_name, src_value)
                )
        elif attribute_type in (
            ods.DataTypeEnum.DT_COMPLEX,
            ods.DataTypeEnum.DS_COMPLEX,
        ):
            for src_value in src_values:
                condition_item.float_array.values.append(float(src_value))
        elif attribute_type in (
            ods.DataTypeEnum.DT_DCOMPLEX,
            ods.DataTypeEnum.DS_DCOMPLEX,
        ):
            for src_value in src_values:
                condition_item.double_array.values.append(float(src_value))
        elif attribute_type in (
            ods.DataTypeEnum.DT_EXTERNALREFERENCE,
            ods.DataTypeEnum.DS_EXTERNALREFERENCE,
        ):
            for src_value in src_values:
                condition_item.string_array.values.append(str(src_value))
        else:
            raise SyntaxError(f"Unable to attach array value for data type '{attribute_type}'.")
    else:
        if attribute_type == ods.DataTypeEnum.DT_BYTE:
            condition_item.byte_array.values = bytes([int(src_values)])
        elif attribute_type == ods.DataTypeEnum.DT_BOOLEAN:
            condition_item.boolean_array.values.append(bool(src_values))
        elif attribute_type == ods.DataTypeEnum.DT_SHORT:
            condition_item.long_array.values.append(int(src_values))
        elif attribute_type == ods.DataTypeEnum.DT_LONG:
            condition_item.long_array.values.append(int(src_values))
        elif attribute_type == ods.DataTypeEnum.DT_LONGLONG:
            condition_item.longlong_array.values.append(int(src_values))
        elif attribute_type == ods.DataTypeEnum.DT_FLOAT:
            condition_item.float_array.values.append(float(src_values))
        elif attribute_type == ods.DataTypeEnum.DT_DOUBLE:
            condition_item.double_array.values.append(float(src_values))
        elif attribute_type == ods.DataTypeEnum.DT_DATE:
            condition_item.string_array.values.append(_jo_date(src_values))
        elif attribute_type == ods.DataTypeEnum.DT_STRING:
            condition_item.string_array.values.append(str(src_values))
        elif attribute_type == ods.DataTypeEnum.DT_ENUM:
            condition_item.long_array.values.append(
                _jo_enum_get_numeric_value(model, attribute_entity, attribute_name, src_values)
            )
        else:
            raise SyntaxError(f"Unable to attach value '{src_values}' for data type '{attribute_type}'.")


def _get_ods_operator(
    attribute_type: ods.DataTypeEnum,
    condition_operator: OperatorEnum,
    condition_options: str,
) -> OperatorEnum:
    if attribute_type in (ods.DataTypeEnum.DT_STRING, ods.DataTypeEnum.DS_STRING):
        if -1 != condition_options.find("i"):
            # check if there is an CI operator
            if condition_operator in _jo_operators_ci_map:
                return _jo_operators_ci_map[condition_operator]

    return condition_operator


def _add_condition(
    model: ods.Model,
    entity: ods.Model.Entity,
    target: ods.SelectStatement,
    condition_path: str,
    condition_operator: OperatorEnum,
    condition_operand_value: list[Any] | Any,
    condition_unit_id: int,
    condition_options: str,
) -> None:
    attribute_type, attribute_name, attribute_entity = _parse_path_and_add_joins(
        model, entity, condition_path, target.joins
    )
    condition_item = target.where.add()
    condition_item.condition.aid = attribute_entity.aid
    condition_item.condition.attribute = attribute_name
    condition_item.condition.operator = _get_ods_operator(attribute_type, condition_operator, condition_options)
    condition_item.condition.unit_id = int(condition_unit_id)
    if condition_item.condition.operator not in (
        OperatorEnum.OP_IS_NULL,
        OperatorEnum.OP_IS_NOT_NULL,
    ):
        _set_condition_value(
            model,
            attribute_entity,
            attribute_name,
            attribute_type,
            condition_operand_value,
            condition_item.condition,
        )


def _parse_conditions(
    model: ods.Model,
    entity: ods.Model.Entity,
    target: ods.SelectStatement,
    element_dict: dict,
    attribute_dict: dict,
) -> None:
    for elem in element_dict:
        elem_attribute = attribute_dict.copy()
        if "$options" in element_dict:
            elem_attribute["options"] = element_dict["$options"]

        if elem.startswith("$"):
            if elem in _jo_operators:
                elem_attribute["operator"] = _jo_operators[elem]
            elif "$unit" == elem:
                elem_attribute["unit"] = element_dict[elem]
            elif "$and" == elem:
                _parse_conditions_conjunction(
                    model,
                    entity,
                    ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_AND,
                    target,
                    element_dict[elem],
                    attribute_dict,
                )
                attribute_dict["conjunction_count"] = attribute_dict["conjunction_count"] + 1
                continue
            elif "$or" == elem:
                _parse_conditions_conjunction(
                    model,
                    entity,
                    ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_OR,
                    target,
                    element_dict[elem],
                    attribute_dict,
                )
                attribute_dict["conjunction_count"] = attribute_dict["conjunction_count"] + 1
                continue
            elif "$not" == elem:
                _parse_conditions_not(model, entity, target, element_dict[elem], attribute_dict)
                attribute_dict["conjunction_count"] = attribute_dict["conjunction_count"] + 1
                continue
            elif "$options" == elem:
                continue
            else:
                raise SyntaxError(f"Unknown operator '{elem}'.{_model_get_suggestion_operators(elem)}")
        else:
            if elem_attribute["path"]:
                elem_attribute["path"] += "."
            elem_attribute["path"] += elem

        if isinstance(element_dict[elem], dict):
            # Check if this is a nested statement structure before recursion
            if len(element_dict[elem]) == 1 and "$nested" in element_dict[elem]:
                # This is a nested statement, handle it specially
                current_operator = elem_attribute.get("operator")
                if current_operator in (OperatorEnum.OP_IS_NULL, OperatorEnum.OP_IS_NOT_NULL):
                    raise SyntaxError("$nested cannot be used with $null or $notnull operators.")

                if 0 != attribute_dict["conjunction_count"]:
                    target.where.add().conjunction = elem_attribute["conjunction"]

                _handle_nested_statement(
                    model,
                    entity,
                    target,
                    elem_attribute["path"],
                    element_dict[elem]["$nested"],
                    elem_attribute["unit"],
                    elem_attribute["options"],
                    elem_attribute.get("operator", OperatorEnum.OP_EQ),
                )
                attribute_dict["conjunction_count"] = attribute_dict["conjunction_count"] + 1
            else:
                # Regular dictionary processing
                old_conjunction_count = elem_attribute["conjunction_count"]
                _parse_conditions(model, entity, target, element_dict[elem], elem_attribute)
                if old_conjunction_count != elem_attribute["conjunction_count"]:
                    attribute_dict["conjunction_count"] = attribute_dict["conjunction_count"] + 1
        else:
            if 0 != attribute_dict["conjunction_count"]:
                target.where.add().conjunction = elem_attribute["conjunction"]

            condition_path = elem_attribute["path"]
            condition_operator = elem_attribute["operator"]
            condition_operand_value = element_dict[elem]
            condition_options = elem_attribute["options"]
            condition_unit_id = elem_attribute["unit"]

            _add_condition(
                model,
                entity,
                target,
                condition_path,
                condition_operator,
                condition_operand_value,
                condition_unit_id,
                condition_options,
            )
            attribute_dict["conjunction_count"] = attribute_dict["conjunction_count"] + 1


def _top_elem_get_suggestion(str_val: str) -> str:
    available = {k: k for k in ["$attributes", "$orderby", "$groupby", "$options"]}
    return _model_get_suggestion(available, str_val)


def _jaquel_to_ods_internal(model: ods.Model, jaquel_query: str | dict) -> JaquelConversionResult:
    """
    Convert a given JAQueL query into an ASAM ODS SelectStatement and collect attribute tuples.

    :param ods.Model model: application model to be used for conversion.
    :param str | dict jaquel_query: JAQueL query as dict or json string.
    :raises SyntaxError: If contains syntactical errors.
    :raises ValueError: If conversion fail.
    :raises json.decoder.JSONDecodeError: If JSON string contains syntax errors.
    :return JaquelConversionResult: A result object containing the target entity, the ASAM ODS SelectStatement,
             and a list of tuples containing attribute paths and their corresponding AttributeItems
    """
    if isinstance(jaquel_query, dict):
        query = jaquel_query
    else:
        query = json.loads(jaquel_query)

    if not isinstance(query, dict):
        raise SyntaxError(f"Invalid JAQueL query format '{type(query)}' only dict allowed.")

    entity = None
    aid = None

    select_statement = ods.SelectStatement()

    # Create a list to collect attribute path and attribute item tuples
    result_column_lookup: list[JaquelConversionResult.Column] = []

    # first parse conditions to get entity
    for elem in query:
        if not (isinstance(elem, str) and elem.startswith("$")):
            if entity is not None:
                raise SyntaxError(f"Only one start point allowed '{elem}'.{_top_elem_get_suggestion(elem)}")

            entity = _model_get_entity_ex(model, elem)
            aid = entity.aid
            if isinstance(query[elem], dict):
                _parse_conditions(
                    model,
                    entity,
                    select_statement,
                    query[elem],
                    {
                        "conjunction": ods.SelectStatement.ConditionItem.ConjuctionEnum.CO_AND,
                        "conjunction_count": 0,
                        "path": "",
                        "operator": OperatorEnum.OP_EQ,
                        "options": "",
                        "unit": 0,
                    },
                )
            else:
                _id_value = query[elem]
                if isinstance(_id_value, str) and not _id_value.isdigit():
                    raise SyntaxError(f"Only id value can be assigned directly. But '{_id_value}' was assigned.")
                # id given
                _add_condition(
                    model,
                    entity,
                    select_statement,
                    "id",
                    OperatorEnum.OP_EQ,
                    int(_id_value),
                    0,
                    "",
                )

    if entity is None or aid is None:
        raise SyntaxError(
            "Does not define a target entity. Dictionary must contain at least one entity base or application name."
        )

    # parse the others
    for elem in query:
        if elem.startswith("$"):
            if "$attributes" == elem:
                _parse_attributes(
                    model,
                    entity,
                    select_statement,
                    query[elem],
                    {"path": "", "aggregate": ods.AggregateEnum.AG_NONE, "unit": 0},
                    result_column_lookup,
                )
            elif "$orderby" == elem:
                _parse_orderby(model, entity, select_statement, query[elem], {"path": ""})
            elif "$groupby" == elem:
                _parse_groupby(model, entity, select_statement, query[elem], {"path": ""})
            elif "$options" == elem:
                _parse_global_options(query[elem], select_statement)
            else:
                raise SyntaxError(f"Unknown first level define '{elem}'.{_top_elem_get_suggestion(elem)}")

    if 0 == len(select_statement.columns):
        select_statement.columns.add(aid=aid, attribute="*")
        result_column_lookup.append(
            JaquelConversionResult.Column(
                aid=aid,
                name="*",
                aggregate=ods.AggregateEnum.AG_NONE,
                path="*",
            )
        )

    return JaquelConversionResult(entity=entity, select_statement=select_statement, column_lookup=result_column_lookup)


def jaquel_to_ods(model: ods.Model, jaquel_query: str | dict) -> tuple[ods.Model.Entity, ods.SelectStatement]:
    """
    Convert a given JAQueL query into an ASAM ODS SelectStatement.

    :param ods.Model model: application model to be used for conversion.
    :param str | dict jaquel_query: JAQueL query as dict or json string.
    :raises SyntaxError: If contains syntactical errors.
    :raises ValueError: If conversion fail.
    :raises json.decoder.JSONDecodeError: If JSON string contains syntax errors.
    :return Tuple[ods.Model.Entity, ods.SelectStatement]: A tuple defining the target entity
        and the ASAM ODS SelectStatement
    """
    result = _jaquel_to_ods_internal(model, jaquel_query)
    return result.entity, result.select_statement


class Jaquel(JaquelConversionResult):
    """
    A class representing the result of converting a JAQueL query into an ASAM ODS SelectStatement.

    This class extends JaquelConversionResult and encapsulates the target entity,
    the ASAM ODS SelectStatement, and a list of tuples containing attribute paths
    and their corresponding AttributeItems.
    """

    def __init__(self, model: ods.Model, jaquel_query: str | dict) -> None:
        """
        Initialize the Jaquel object by converting the given JAQueL query.

        :param ods.Model model: application model to be used for conversion.
        :param str | dict jaquel_query: JAQueL query as dict or json string.
        :raises SyntaxError: If contains syntactical errors.
        :raises ValueError: If conversion fail.
        :raises json.decoder.JSONDecodeError: If JSON string contains syntax errors.
        """
        result = _jaquel_to_ods_internal(model, jaquel_query)
        super().__init__(
            entity=result.entity,
            select_statement=result.select_statement,
            column_lookup=result.column_lookup,
        )
