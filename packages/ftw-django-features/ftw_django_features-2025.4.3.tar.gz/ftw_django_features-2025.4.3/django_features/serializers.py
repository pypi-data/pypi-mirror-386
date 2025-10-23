from typing import Any

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import FieldDoesNotExist
from django.core.exceptions import ValidationError
from django.db import models
from rest_framework.fields import empty
from rest_framework.relations import ManyRelatedField

from django_features.custom_fields.serializers import CustomFieldBaseModelSerializer
from django_features.fields import UUIDRelatedField


class ExternalUUIDRelatedField(UUIDRelatedField):
    default_uuid_field_name = "external_uid"


class BaseMappingSerializer(CustomFieldBaseModelSerializer):
    related_fields: set[str] = set()
    relation_separator: str = "."
    serializer_related_field = ExternalUUIDRelatedField
    _write_only_serializer = True

    class Meta:
        abstract = True
        fields = "__all__"
        model = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._unique_choice_field = str(
            self.mapping.get("unique_choice_field", "value")
        )
        super().__init__(*args, **kwargs)
        self.exclude: list[str] = []

    @property
    def mapping(self) -> dict[str, dict[str, Any]]:
        raise NotImplementedError("Mapping must be set")

    @property
    def mapping_fields(self) -> list[str]:
        raise NotImplementedError("Mapping fields must be set")

    @property
    def model(self) -> models.Model:
        if self.Meta.model is None:
            raise ValueError("Meta.model must be set")
        return self.Meta.model

    def get_fields(self) -> dict[str, Any]:
        initial_fields = super().get_fields()
        fields: dict[str, Any] = dict()
        nested_fields: dict[str, Any] = dict()
        nested_field_fields: dict[str, list[str]] = dict()
        nested_field_data: dict[str, Any] = dict()
        for internal_name in self.mapping_fields:
            if internal_name in self.exclude:
                continue
            split = internal_name.split(self.relation_separator)
            field_name = split[0]
            serializer_field = initial_fields.get(field_name)
            if serializer_field is not None and len(split) == 1:
                fields[internal_name] = serializer_field
            else:
                try:
                    field = self.model._meta.get_field(field_name)
                except FieldDoesNotExist:
                    raise ValidationError(
                        f"Invalid field '{field_name}' for model {self.model}."
                    )

                if len(split) > 1:
                    nested_field = self.relation_separator.join(split[1:])
                    if field_name not in nested_fields:
                        nested_fields[field_name] = field
                    if field_name in nested_field_data:
                        nested_field_data[field_name][nested_field] = self.initial_data[
                            internal_name
                        ]
                    elif internal_name in self.initial_data:
                        nested_field_data[field_name] = {
                            nested_field: self.initial_data[internal_name]
                        }
                    if field_name in nested_field_fields:
                        nested_field_fields[field_name].append(nested_field)
                    else:
                        nested_field_fields[field_name] = [nested_field]
                elif isinstance(field, GenericRelation):
                    self.related_fields.add(field_name)
                    fields[internal_name] = ManyRelatedField(
                        child_relation=ExternalUUIDRelatedField(
                            field=field, required=False
                        ),
                        required=False,
                    )
        for field_name, field in nested_fields.items():
            self.related_fields.add(field_name)
            fields[field_name] = NestedMappingSerializer(
                data=nested_field_data[field_name],
                exclude=[*self.exclude, self.model.__name__.lower()],
                field=field,
                nested_fields=nested_field_fields[field_name],
                parent_mapping=self.mapping,
                required=False,
            )
        missing_declared_fields = self._declared_fields.keys() - fields.keys()
        fields.update(
            {field: initial_fields[field] for field in missing_declared_fields}
        )
        self.fields = fields
        return fields

    def create(self, validated_data: dict[str, Any]) -> models.Model:
        relations_to_save: dict[str, Any] = {}
        for field in self.related_fields:
            value = validated_data.pop(field, None)
            if value is not None:
                relations_to_save[field] = value
            else:
                serializer = self.fields.get(field)
                if serializer is not None:
                    serializer.is_valid(raise_exception=True)
                    relations_to_save[field] = serializer.save()
        instance = super().create(validated_data)
        for field, value in relations_to_save.items():
            model_field = self.model._meta.get_field(field)
            if model_field.many_to_many or model_field.one_to_many:
                getattr(instance, field).set(value)
            if model_field.one_to_one or model_field.many_to_one:
                setattr(instance, field, value)
        instance.save()
        return instance

    def update(
        self, instance: models.Model, validated_data: dict[str, Any]
    ) -> models.Model:
        for field in self.related_fields:
            value = validated_data.pop(field, None)
            if value is None:
                serializer = self.fields[field]
                serializer.is_valid(raise_exception=True)
                value = serializer.save()
            model_field = self.model._meta.get_field(field)
            if model_field.many_to_many or model_field.one_to_many:
                getattr(instance, field).set(value)
            if model_field.one_to_one or model_field.many_to_one:
                setattr(instance, field, value)
        return super().update(instance, validated_data)


class NestedMappingSerializer(BaseMappingSerializer):
    class Meta:
        fields = "__all__"
        model = None

    def __init__(
        self,
        exclude: list,
        field: models.Field,
        nested_fields: list,
        parent_mapping: dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.exclude = exclude
        self.nested_fields = nested_fields
        self.parent_mapping = parent_mapping
        self.Meta.model = field.related_model
        super().__init__(*args, **kwargs)

    @property
    def mapping(self) -> dict[str, dict[str, Any]]:
        return self.parent_mapping

    @property
    def mapping_fields(self) -> list[str]:
        return self.nested_fields


class MappingSerializer(BaseMappingSerializer):
    _format_prefix = "format"

    class Meta:
        abstract = True
        fields = "__all__"
        model = None

    def __init__(
        self,
        instance: Any = None,
        data: Any = empty,
        **kwargs: Any,
    ) -> None:
        mapped_data = self.map_data(data)
        super().__init__(instance, data=mapped_data, **kwargs)

    def _get_nested_data(self, field_path: list[str], data: Any) -> Any:
        field_name = field_path[0]
        if data is not None and field_name in data:
            if len(field_path) > 1:
                return self._get_nested_data(field_path[1:], data[field_name])
            else:
                return data[field_name]
        return None

    def map_data(self, data: Any) -> Any:
        for external_name, internal_name in self.model_mapping.items():
            field_path = external_name.split(self.relation_separator)
            value = self._get_nested_data(field_path, data)
            if value is None:
                continue
            format_func = getattr(self, f"{self._format_prefix}_{internal_name}", None)
            if format_func is not None:
                value = format_func(value)
            data[internal_name] = value
        return data

    @property
    def mapping_fields(self) -> list[str]:
        return list(self.model_mapping.values())

    @property
    def model_mapping(self) -> dict[str, Any]:
        mapping = getattr(self, "mapping", None)
        if mapping is None:
            raise ValueError("Mapping must be set")
        return mapping.get(self.model.__name__.lower(), {})
