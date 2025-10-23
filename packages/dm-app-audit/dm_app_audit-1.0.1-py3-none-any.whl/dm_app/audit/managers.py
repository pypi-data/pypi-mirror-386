from django.apps import apps
from django.db import models
from uuid import uuid4


class ResourceUserGroupManager(models.Manager):

    def register_user(self, user, resource_id=uuid4().hex[:24], group=None, template='OWNER'):
        """
        Register user
        """
        default_app_permission_template_model = apps.get_model('dm_app_authz', 'DefaultAppPermissionTemplateModel')
        group_resource_permission_model = apps.get_model('dm_app_authz', 'GroupResourcePermissionModel')
        permission_template = default_app_permission_template_model.objects.get(name=template)
        if group is None:
            group = group_resource_permission_model.objects.create(resource_id=resource_id,
                                                                   permissions=permission_template.permissions,
                                                                   name=permission_template.name)
        instance = self.model.objects.create(user_id=user['id'], resource_id=resource_id, group=group)
        return instance

    def get_resource_groups(self, user_id):
        """
        Return all the resource_id, group_id related to user_id
        """
        return self.model.objects.filter(user_id=user_id)

    def get_last_accessed_resource_group(self, user_id):
        """
        Return last accessed resource_id, group_id related to user_id
        """
        return self.model.objects.order_by('-last_accessed').filter(user_id=user_id).first()