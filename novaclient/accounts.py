from novaclient import base

class Account(base.Resource):
    pass

class AccountManager(base.BootingManagerWithFind):
    resource_class = Account

    def create_instance_for(self, account_id, name, image, flavor,
            ipgroup=None, meta=None, files=None, zone_blob=None,
            reservation_id=None):
        resource_url = "/accounts/%s/create_instance" % account_id
        return self._boot(resource_url, "server", name, image, flavor,
                          ipgroup=ipgroup, meta=meta, files=files,
                          zone_blob=zone_blob, reservation_id=reservation_id)
