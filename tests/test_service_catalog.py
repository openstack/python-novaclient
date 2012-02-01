from novaclient import exceptions
from novaclient import service_catalog
from tests import utils


# Taken directly from keystone/content/common/samples/auth.json
# Do not edit this structure. Instead, grab the latest from there.

SERVICE_CATALOG = {
    "access": {
        "token": {
            "id": "ab48a9efdfedb23ty3494",
            "expires": "2010-11-01T03:32:15-05:00",
            "tenant": {
                "id": "345",
                "name": "My Project"
            }
        },
        "user": {
            "id": "123",
            "name": "jqsmith",
            "roles": [
                {
                    "id": "234",
                    "name": "compute:admin",
                },
                {
                    "id": "235",
                    "name": "object-store:admin",
                    "tenantId": "1",
                }
            ],
            "roles_links": [],
        },
        "serviceCatalog": [
            {
                "name": "Cloud Servers",
                "type": "compute",
                "endpoints": [
                    {
                        "tenantId": "1",
                        "publicURL": "https://compute1.host/v1/1234",
                        "internalURL": "https://compute1.host/v1/1234",
                        "region": "North",
                        "versionId": "1.0",
                        "versionInfo": "https://compute1.host/v1.0/",
                        "versionList": "https://compute1.host/"
                    },
                    {
                        "tenantId": "2",
                        "publicURL": "https://compute1.host/v1.1/3456",
                        "internalURL": "https://compute1.host/v1.1/3456",
                        "region": "North",
                        "versionId": "1.1",
                        "versionInfo": "https://compute1.host/v1.1/",
                        "versionList": "https://compute1.host/"
                    },
                ],
                "endpoints_links": [],
            },
            {
                "name": "Cloud Files",
                "type": "object-store",
                "endpoints": [
                    {
                        "tenantId": "11",
                        "publicURL": "https://compute1.host/v1/blah-blah",
                        "internalURL": "https://compute1.host/v1/blah-blah",
                        "region": "South",
                        "versionId": "1.0",
                        "versionInfo": "uri",
                        "versionList": "uri"
                    },
                    {
                        "tenantId": "2",
                        "publicURL": "https://compute1.host/v1.1/blah-blah",
                        "internalURL": "https://compute1.host/v1.1/blah-blah",
                        "region": "South",
                        "versionId": "1.1",
                        "versionInfo": "https://compute1.host/v1.1/",
                        "versionList": "https://compute1.host/"
                    },
                ],
                "endpoints_links": [
                    {
                        "rel": "next",
                        "href": "https://identity1.host/v2.0/endpoints"
                    },
                ],
            },
        ],
        "serviceCatalog_links": [
            {
                "rel": "next",
                "href": "https://identity.host/v2.0/endpoints?session=2hfh8Ar",
            },
        ],
    },
}


class ServiceCatalogTest(utils.TestCase):
    def test_building_a_service_catalog(self):
        sc = service_catalog.ServiceCatalog(SERVICE_CATALOG)

        self.assertRaises(exceptions.AmbiguousEndpoints, sc.url_for)
        self.assertEquals(sc.url_for('tenantId', '1'),
                            "https://compute1.host/v1/1234")
        self.assertEquals(sc.url_for('tenantId', '2'),
                            "https://compute1.host/v1.1/3456")

        self.assertRaises(exceptions.EndpointNotFound,
                                        sc.url_for, "region", "South")
