from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.inventory import DeviceCreate, SiteCreate


def test_site_code_is_normalized() -> None:
    site = SiteCreate(name=" Core ", code=" core-1 ", region="west")
    assert site.code == "CORE-1"
    assert site.name == "Core"


def test_device_rejects_invalid_management_ip() -> None:
    with pytest.raises(ValidationError):
        DeviceCreate(
            name="edge", hostname="edge-1", management_ip="not-an-ip",
            device_type="EDGE_ROUTER", site_id=uuid4(),
        )
