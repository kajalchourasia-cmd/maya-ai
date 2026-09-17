import copy
import math

import pytest

from scripts.maya_local_database import bindings_are_loopback
from scripts.repair_maya_loopback import create_payload, NETWORK, PROJECT
from scripts.check_maya_vector_roundtrip import cosine, validate_vectors
from scripts.check_maya_local_services import safe_studio_redirect


def test_studio_redirect_is_followed_only_on_its_exact_local_origin():
    assert safe_studio_redirect("http://127.0.0.1:54323/", "/project/default") == "http://127.0.0.1:54323/project/default"
    for location in ("https://example.com", "http://127.0.0.1:54321/", "//example.com/", "http://user@127.0.0.1:54323/"):
        with pytest.raises(ValueError):
            safe_studio_redirect("http://127.0.0.1:54323/", location)


def container_fixture():
    return {"State": {"Running": False},
            "Config": {"Labels": {"com.supabase.cli.project": PROJECT}, "Env": ["TEST=not-a-real-secret"]},
            "HostConfig": {"NetworkMode": NETWORK, "Binds": ["preserved:/data"],
                           "PortBindings": {"5432/tcp": [{"HostIp": "", "HostPort": "54322"}]}},
            "NetworkSettings": {"Networks": {NETWORK: {"Aliases": ["db"], "IPAddress": "172.18.0.2"}}}}


def test_repair_preserves_configuration_and_does_not_mutate_inspection():
    original = container_fixture()
    before = copy.deepcopy(original)
    payload = create_payload(original)
    assert original == before
    assert payload["Env"] == original["Config"]["Env"]
    assert payload["HostConfig"]["Binds"] == ["preserved:/data"]
    assert payload["HostConfig"]["PortBindings"]["5432/tcp"] == [{"HostIp": "127.0.0.1", "HostPort": "54322"}]
    assert payload["NetworkingConfig"]["EndpointsConfig"][NETWORK] == {"Aliases": ["db"]}


@pytest.mark.parametrize("change", ["running", "other_project", "other_network"])
def test_repair_refuses_out_of_scope_container(change):
    original = container_fixture()
    if change == "running":
        original["State"]["Running"] = True
    elif change == "other_project":
        original["Config"]["Labels"]["com.supabase.cli.project"] = "unrelated"
    else:
        original["HostConfig"]["NetworkMode"] = "bridge"
    with pytest.raises(ValueError):
        create_payload(original)


@pytest.mark.parametrize("ports", [{}, {"5432/tcp": None}, {"5432/tcp": []},
    {"5432/tcp": [{"HostIp": "0.0.0.0"}]}, {"5432/tcp": [{"HostIp": "127.0.0.1"}, {"HostIp": "::"}]}])
def test_no_false_loopback_pass_for_empty_or_broad_ports(ports):
    assert not bindings_are_loopback(ports)


def test_real_loopback_ports_pass():
    assert bindings_are_loopback({"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "54322"}]})


def test_independent_cosine():
    assert cosine([1, 0], [1, 0]) == 1
    assert cosine([1, 0], [0, 1]) == 0
    assert cosine([1, 1], [1, 0]) == pytest.approx(1/math.sqrt(2))


@pytest.mark.parametrize("bad", [[0.0] * 1536, [0.1] * 32, [float('nan')] * 1536, [True] * 1536])
def test_invalid_saved_vectors_are_not_treated_as_real_compatible_embeddings(bad):
    with pytest.raises(ValueError):
        validate_vectors({"model": "text-embedding-3-small", "dimensions": 1536, "vectors": [bad] * 3})
