from temperpi import network


def test_prefers_eth0(monkeypatch):
    addrs = {"wlan0": "10.0.0.5", "eth0": "192.168.1.10"}
    monkeypatch.setattr(
        network.socket, "if_nameindex", lambda: [(1, "lo"), (2, "wlan0"), (3, "eth0")]
    )
    monkeypatch.setattr(network, "interface_ipv4", addrs.get)
    assert network.primary_ipv4(["eth0", "wlan0"]) == "192.168.1.10"


def test_falls_back_to_other_interfaces(monkeypatch):
    addrs = {"lo": "127.0.0.1", "usb0": "172.16.0.2"}
    monkeypatch.setattr(network.socket, "if_nameindex", lambda: [(1, "lo"), (2, "usb0")])
    monkeypatch.setattr(network, "interface_ipv4", addrs.get)
    assert network.primary_ipv4(["eth0"]) == "172.16.0.2"


def test_no_address(monkeypatch):
    monkeypatch.setattr(network.socket, "if_nameindex", lambda: [(1, "lo")])
    monkeypatch.setattr(network, "interface_ipv4", lambda _n: None)
    assert network.primary_ipv4() == network.NO_IPV4


def test_loopback_lookup_works():
    assert network.interface_ipv4("lo") == "127.0.0.1"
    assert network.interface_ipv4("definitely-not-an-iface") is None
