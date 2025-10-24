from loopbot.permissions import Permission, PermissionLevel


def test_permission_defaults_and_to_dict():
    p = Permission()
    data = p.to_dict()
    assert data["edit"] == PermissionLevel.ALLOW
    assert data["webfetch"] == PermissionLevel.DENY
    assert data["bash"] == PermissionLevel.DENY


def test_permission_bash_dict_override_serializes():
    p = Permission(bash={"python": Permission.ALLOW, "rm": Permission.DENY})
    data = p.to_dict()
    assert isinstance(data["bash"], dict)
    assert data["bash"]["python"] == PermissionLevel.ALLOW
    assert data["bash"]["rm"] == PermissionLevel.DENY
