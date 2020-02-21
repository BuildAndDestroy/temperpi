#!/usr/bin/env python3
"""Pull the ip from internet connected interfaces.

Current list is of internet connected interfaces. More can be added as needed.
Eth0 is the primary interface that will report. This can be changes in the
return_ipv4_address function, specifically the generator.
"etho" = <whatever interface you prefer>
"""

import netifaces


def create_interfaces_list() -> list:
    """Grab eth0 and wlan0."""
    interfaces = []

    for machine_interfaces in netifaces.interfaces():
        if machine_interfaces == "eth0":  # Standard eth interface
            interfaces.append(machine_interfaces)
        if machine_interfaces == "wlan0":  # Standard wifi interface
            interfaces.append(machine_interfaces)
        if machine_interfaces == "enp3s0":
            interfaces.append(machine_interfaces)
        if machine_interfaces == "wlp2s0":
            interfaces.append(machine_interfaces)

    return interfaces


def interface_and_ips(interfaces_list) -> dict:
    """Checks for IPv4, anything less than or equal to 14 characters."""
    interface_dict = {}

    for interface in interfaces_list:
        for key, value in netifaces.ifaddresses(interface).items():
            for returned_lists in value:
                if len(returned_lists.get('addr')) <= 14:
                    interface_dict[interface] = returned_lists.get('addr')

    return interface_dict


def return_ipv4_address(dict_of_interfaces) -> str:
    """Filter out for eth0 first, the return the next interfaces IPv4."""
    interfaces = list(dict_of_interfaces.keys())

    etho_interface = ['{}'.format(
        value) for key, value in dict_of_interfaces.items() if key == "eth0"]
    if etho_interface:
        return etho_interface[0]

    for index in interfaces:
        for key, value in dict_of_interfaces.items():
            if key == index:
                return value
    if not interfaces:
        return 'No IPv4!'


def main() -> None:
    """Execute the main function."""
    list_of_interfaces = create_interfaces_list()
    dict_of_ipv4_interfaces = interface_and_ips(list_of_interfaces)
    ipvfour_address = return_ipv4_address(dict_of_ipv4_interfaces)
    print(ipvfour_address)


if __name__ == '__main__':
    main()
