import json
import pprint

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from rest_framework import serializers


class NameOnlySerializer(serializers.Serializer):
    name = serializers.CharField
    id = serializers.IntegerField()


class RelatedNameDictField(serializers.RelatedField):

    def __init__(self, lookup_field="id", extra_fields=['name'], writable=False, types={}, **kwargs):
        super(RelatedNameDictField, self).__init__(**kwargs)
        self.lookup_field = lookup_field
        self.extra_fields = extra_fields
        self.writable = writable
        self.types = types

    def to_representation(self, value):
        result = {self.lookup_field: getattr(value, self.lookup_field)}
        for field in self.extra_fields:
            if '__' in field:
                splitted = field.split('__')
                obj = getattr(value, splitted[0])
                for i in range(1, len(splitted)):
                    if hasattr(obj, splitted[i]):
                        obj = getattr(obj, splitted[i])
                    else:
                        obj = None
                        break
                result[field] = obj
            else:
                result[field] = getattr(value, field)
        return result

    def to_internal_value(self, data):
        if isinstance(data, str):
            datadict = json.loads(data)
        else:
            datadict = data
        if self.writable:
            return datadict
        return self.queryset.get(**{self.lookup_field: datadict[self.lookup_field]})


class RelatedDictFieldFix(OpenApiSerializerFieldExtension):
    target_class = 'config      .serializers.RelatedNameDictField'

    def map_serializer_field(self, auto_schema, direction):
        properties = {'id': {
            'type': "integer",
            'required': 'true'
        }}
        for f in self.target.extra_fields:
            typ = "string"
            if f in self.target.types:
                typ = self.target.types[f]
            properties[f] = {
                "type": typ
            }
        title = "RelatedDictionary" if not self.target.writable else "Writable Related Dictionary"
        return {'type': "object",
                "title": title,
                "properties": properties
                }


def set_related(model, instance, field, related_data, related_field):
    try:
        other_field = model._meta.get_field(related_field)
        if getattr(other_field, 'blank', False) or getattr(other_field, 'required', True):
            related_data[related_field] = instance
            related = model._default_manager.create(**related_data)
            related.save()
        else:
            related = model._default_manager.create(**related_data)
            setattr(instance, field, related)
            related.save()
            instance.save()
    except Exception as e:
        related = model._default_manager.create(**related_data)
        setattr(instance, field, related)
        related.save()
        instance.save()
    return related


class NestedSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        nested_items = {}
        for field in self.Meta.nested_fields:
            if field in validated_data:
                if validated_data[field]:
                    nested_items[field] = validated_data.pop(field)
                else:
                    validated_data.pop(field)
        instance = super(NestedSerializer, self).create(validated_data)
        for field in nested_items:
            model = self.Meta.nested_fields[field]
            if isinstance(nested_items[field], list):
                for item in nested_items[field]:
                    set_related(model, instance, field, item,
                                self.Meta.related_field)
            else:
                set_related(model, instance, field,
                            nested_items[field], self.Meta.related_field)
        return instance

    def create_or_update(self, props, model, field, instance, related_field):
        if 'id' in props:
            item = model.objects.get(id=props['id'])
            props.pop('id')
            for key in props:
                try:
                    setattr(item, key, props[key])
                except Exception:
                    pass
        else:
            item = set_related(model, instance, field, props, related_field)
        item.save()
        return item

    def update(self, instance, validated_data):
        nested_items = {}
        for field in self.Meta.nested_fields:
            if field in validated_data:
                if validated_data[field]:
                    nested_items[field] = validated_data.pop(field)
                else:
                    validated_data.pop(field)
                    if hasattr(instance, field) and getattr(instance, field):
                        try:
                            getattr(instance, field).delete()
                        except Exception:
                            getattr(instance, field).all().delete()
        instance = super(NestedSerializer, self).update(
            instance, validated_data)
        for field in nested_items:
            model = self.Meta.nested_fields[field]
            if isinstance(nested_items[field], list):
                ids = []
                for item in nested_items[field]:
                    obj = self.create_or_update(
                        item, model, field, instance, self.Meta.related_field)
                    ids.append(obj.id)
                qs = getattr(instance, field).exclude(pk__in=ids)
                if qs:
                    qs.delete()
            else:
                self.create_or_update(
                    nested_items[field], model, field, instance, self.Meta.related_field)
        return instance

    class Meta:
        abstract = True


# Example Use

# class AdminCourseSerializer(NestedSerializer):
#     subject = RelatedNameDictField(queryset=Subject.objects.all(), extra_fields=[
#                                    'name', 'score', 'duration'])
#     programs = RelatedNameDictField(many=True, queryset=models.Program.objects.all(
#     ), extra_fields=['professor__full_name', 'professor_id'], writable=True)

#     class Meta:
#         model = models.Course
#         fields = "__all__"
#         related_field = 'course' #This is the FK property on the child model that refers to the parent
#         nested_fields = {'programs': models.Program} # This is a thatsets the related model for the writeable properties


# class CompetitionSerializer(NestedSerializer):
#     videogame = RelatedNameDictField(many=False, queryset=models.Videogame.objects.all(
#     ), extra_fields=['name', 'category__name', 'category__id'])
#     devices = RelatedNameDictField(
#         many=True, queryset=models.Device.objects.all())
#     user_level = RelatedNameDictField(
#         many=False, queryset=models.UserLevel.objects.all(), required=False)
#     picture = serializers.FileField(required=False)
#     brand = RelatedNameDictField(many=False, queryset=Brand.objects.all(
#     ), required=False, extra_fields=['name', 'bg', 'fg', 'font', 'logo__url'])
#     sponsors = RelatedNameDictField(many=True, queryset=Brand.objects.all(
#     ), required=False, extra_fields=['name', 'bg', 'fg', 'font', 'logo__url'])
#     payment_league = RelatedNameDictField(many=False, queryset=models.PaymentLeague.objects.all(
#     ), extra_fields=["url", "processor_id", "processor__name"], writable=True)
#     competition_types = serializers.SerializerMethodField()
#     countries = RelatedNameDictField(many=True, queryset=Country.objects.all())
#     requirements = RelatedNameDictField(many=True, queryset=models.Requirement.objects.all(
#     ), extra_fields=['body', 'attachment'], writable=True)
#     classification_stage = RelatedNameDictField(many=False, queryset=models.ClassificationStage.objects.all(
#     ), extra_fields=stage_fields, writable=True, required=False)
#     knockout_stage = RelatedNameDictField(many=False, queryset=models.KnockoutStage.objects.all(
#     ), extra_fields=stage_fields, writable=True, required=False)
#     group_stage = RelatedNameDictField(many=False, queryset=models.GroupStage.objects.all(
#     ), extra_fields=stage_fields + ['group_count'], writable=True, required=False)
#     rounds = RelatedNameDictField(many=True, queryset=models.Round.objects.all(), extra_fields=[
#                                   'index', 'date', 'time'], source="get_rounds", required=False, writable=True)
#     groups = RelatedNameDictField(
#         many=True, read_only=True, source="get_groups")

#     # def validate_classification_stage(self, value):
#     #   init_date = value['init_date']
#     #   end_date = value['end_date']
      # return True or False

#     def get_competition_types(self, obj):
#         response = []
#         for x in models.Competition.CompetitionType:
#             response.append(x)
#         return response

#     class Meta:
#         model = models.Competition
#         fields = "__all__"
#         related_field = 'competition'
#         nested_fields = {'requirements': models.Requirement,
#                          'payment_league': models.PaymentLeague,
#                          'classification_stage': models.ClassificationStage,
#                          'group_stage': models.GroupStage,
#                          'knockout_stage': models.KnockoutStage}
