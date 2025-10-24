import django

django.setup()
from django.contrib.auth.models import Group  # NOQA

from ichec_django_core.models import PortalMember, Organization, Address  # NOQA

_DEFAULT_TYPES = ["member", "group", "organization"]


def create_resources(types: list, count: int = 100):

    if "memberx" in types:
        for idx in range(count):
            PortalMember.objects.create(
                username=f"member_{idx}",
                email=f"member_{idx}@example.com",
                first_name="Script",
                last_name=f"User {idx}",
            )

    if "organizationx" in types:
        for idx in range(100):
            address = Address.objects.create(
                line1="Apartment 123",
                line2="123 Street",
                city="City",
                region="Region",
                postcode="abc123",
                country="IE",
            )
            Organization.objects.create(
                name=f"Organization {idx}",
                acronym=f"ORG {idx}",
                description=f"Description of org {idx}",
                address=address,
                website=f"www.org{idx}.com",
            )
    if "group" in types:
        for idx in range(100):
            _ = Group.objects.create(name=f"Script Group {idx}")


if __name__ == "__main__":

    create_resources(_DEFAULT_TYPES, 100)
