from django.apps import apps
from django.db import models
from solo.models import SingletonModel


class NameField(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class TimeStamp(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ProxyParentModel(models.Model):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if self.object_class and self.object_class != 'app.name_of_parent_table':
        self.__class__ = apps.get_model(self.object_class)

    object_class = models.CharField(max_length=255, default="", blank=True)

    def save(self, *args, **kwargs):
        # if self.object_class != 'app.name_of_parent_table':
        if self.object_class != "":
            self.object_class = self._meta.app_label + '.' + self._meta.model_name
        super(ProxyParentModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True

# Example Use:

# class Stage(ProxyParentModel): #This would be the parent model
#     init_date = models.DateField()

# class ClassificationStage(Stage):
#     def init_stage(self):
#         # Do something that only classification does
#         pass

#     class Meta:
#         proxy = True

# class GroupStage(Stage):
#     def init_stage(self):
#         # Do something that only group stage does
#         pass

#     class Meta:
#         proxy = True

# class KnockoutStage(Stage):
#     def init_stage(self):
#         # Do something that only knockout stage does
#         pass

#     class Meta:
#         proxy = True


class Config(SingletonModel):
    pass
