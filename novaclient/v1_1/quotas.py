from novaclient import base


class QuotaSet(base.Resource):
    def get(self):
        self.manager.get(self)

    def delete(self):
        self.manager.delete(self)

    def update(self, *args, **kwargs):
        self.manager.update(self.tenant_id, *args, **kwargs)


class QuotaSetManager(base.ManagerWithFind):
    resource_class = QuotaSet

    def list(self, defaults=False):
        if defaults == True:
            return self._list('/os-quotas?defaults=True',
                              'quota_set_list')
        else:
            return self._list("/os-quotas", "quota_set_list")

    def get(self, tenant_id):
        if hasattr(tenant_id, 'tenant_id'):
          tenant_id = tenant_id.tenant_id
        return self._get("/os-quotas/%s" % (tenant_id), "quota_set")

    def update(self, tenant_id, metadata_items=None,
               injected_file_content_bytes=None, volumes=None, gigabytes=None,
               ram=None, floating_ips=None, instances=None, injected_files=None,
               cores=None):

        body = {'quota_set': {
            'tenant_id': tenant_id,
            'metadata_items': metadata_items,
            'injected_file_content_bytes': injected_file_content_bytes,
            'volumes': volumes,
            'gigabytes': gigabytes,
            'ram': ram,
            'floating_ips': floating_ips,
            'instances': instances,
            'injected_files': injected_files,
            'cores': cores,
        }}

        for key in body['quota_set'].keys():
            if body['quota_set'][key] == None:
                body['quota_set'].pop(key)

        return self._update('/os-quotas/%s' % (tenant_id), body)

    def delete(self, tenant_id):
        if hasattr(tenant_id, 'tenant_id'):
          tenant_id = tenant_id.tenant_id
        self._delete("/os-quotas/%s" % (tenant_id))

