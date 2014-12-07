import re
import sys
import argparse
from getpass import getpass
import pprint
import time
import paramiko

""" Project description here:

Summary of the goals:

Author: 

Copyright or opensource license here.
"""
class Junos_Router():
    """
    this class offers support for Cisco IOS Routers.

    Arguments:
        <IPv4_address> string: ipv4 address of the node.

    Returns:
        <router_info> dictionary: contains the parsed info.
            Example = {
                "Model: "      : model,
                "Version: "    : version,
                "RAM: "        : memory,
                "Flash: "      : flash,
                "Free Flash: " : free_flash
                "Linecards: "  : linecard
            }
    """
    pass

class IOS_Router():
    """
    this class offers support for Cisco IOS Routers.

    Arguments:
        <IPv4_address> string: ipv4 address of the node.

    Returns:
        <router_info> dictionary: contains the parsed info.
            Example = {
                "Model: "      : model,
                "Version: "    : version,
                "RAM: "        : memory,
                "Flash: "      : flash,
                "Free Flash: " : free_flash
                "Linecards: "  : linecard
            }
    """

    def __init__(self, username, password, ip_address, enable="enable\n"):
        """ this runs the first time the class is created. """
        self._user = username
        self._pass = password + "\n"
        self._ip_address = ip_address
        self._enable = enable

    def __run_commands(self, commandList, time=5000):
        """ this function runs the specified commands on the node and returns a
        list with unfiltered results.

        Arguments:
            <commandList> list: contains all the command that needs to be
                executed, example:
                    ["show version", "show flash:"]
            <timeout> integer: timeout in seconds for expect.

        Returns:
            <results> list: unfiltered list of command results after execution.
        """
        results = []
        try:
            try:
                print "Connecting to " + senf._ip_address
                remote_conn_pre = paramiko.SSHClient()
                remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                remote_conn_pre.connect(self._ip_address, username=self._user, password=self._pass)
                remote_conn = remote_conn_pre.invoke_shell()
                remote_conn.send(self._enable)
                remote_conn.send(self._pass)
            except AuthenticationException:
                print "Authentication Failed"
            for com in commandList:
                remote_conn.send(com)
                time.sleep(1)
                output = remote_conn.recv(buffer)
                results.append(output)
                remote_conn.send("exit")
        except ProxyCommandFailure:
            print "Error while trying to execute commands."
        return results

    def get_node_info(self):
        """ this is the function that collect the information from the Routers
        and returns them in a dictionary.

        Arguments:
            <None> no arguments are needed, as data is aquired during class init.

        Returns:
            <node_diagram> dictionary: containing all the discovery data:
                example:
                    node_diagram = {
                        "model": model,
                        "sw_version": sw_version,
                        "RAM": total_memory,
                        "flash": total_flash,
                        "free_flash": free_flash,
                        "linecards": {
                            "module1": {
                                "type": linecard_type,
                                "slotname": "WIC",
                            }
                            "module2": {
                            ....
                            }
                        }
                    }
        """
        node_diagram = {}
        commands_to_execute = [
            "terminal length 0\n"
            "show version\n",
            "dir flash:\n",
            "sh diag\n",
        ]
        results = self.__run_commands(commands_to_execute)
        if results:
            # time to get some parsing.
            # show ver command result:
            show_ver_result = results[1]
            # dir flash: command result.
            dir_flash_result = results[2]
            # show diag ? command result.
            show_diag_result = results[3]
            # creating the parsing regexp.
            show_ver_regex = ".*Software\s\((?P<image>.+)\),\sVersion\s(?P<version>.+), RELEASE.*"
            model_regex = ".*Cisco\s(?P<model>\d+).*"
            dir_flash_regex = ".*\n(?P<flash>\d+)\sbytes total\s\((?P<free_flash>\d+)\sbytes free\).*"
            serial_number_regex = ".*Serial number\s+(?P<serial_number>\d+).*"
            total_memory_regex = ".*\s(?P<main>\d+)K/(?P<shared>\d+)K.*"
            # TODO: placing some garbage to test.
            # flash filter.
            try:
                match_flash = re.match(dir_flash_regex, dir_flash_result, re.DOTALL)
                group_flash = match_flash.groupdict()
                total_flash = int(group_flash["flash"])
                free_flash = int(group_flash["free_flash"])
                node_diagram["flash"] = total_flash
                node_diagram["free_flash"] = free_flash
            except AttributeError:
                print "There might be some issue with the 'dir flash:' output."

            # total_memory filter.
            try:
                match_total_memory = re.match(total_memory_regex, show_ver_result, re.DOTALL)
                group_memory = match_total_memory.groupdict()
                main_memory = int(group_memory["main"])
                shared_memory = int(group_memory["shared"])
                total_memory = main_memory + shared_memory
                node_diagram["RAM"] = total_memory
            except AttributeError:
                print "There might be some issue with the RAM memory value into the 'show version' output."

            # model filter.
            try:
                match_model = re.match(model_regex, show_ver_result, re.DOTALL)
                group_model = match_model.groupdict()
                node_diagram["model"] = group_model["model"]
            except AttributeError:
                print "There might be some issue with the Model value into the 'show version' output."

            # version filter.
            try:
                match_version = re.match(show_ver_regex, show_ver_result, re.DOTALL)
                group_version = match_version.groupdict()
                image = group_version["image"]
                version = group_version["version"]
                node_diagram["version"] = image, version
            except AttributeError:
                print "There might be some issue with the Version value int the 'show version' output."

            # diag filter.
            """since we still don't know how many slots exist in our device, we loop the 'show diag' result
            looking for a 'Slot #' match, assigning the last result to the max variable. Then we are able to filter 
            serial numbers and linecards type."""
            try:
                module = {}
                for i in range(0, 20):
                    slot = "Slot %d" % i
                    if slot in show_diag_result:
                       max = i
                for slot_number in range(0, max+1):
                    regex = ".*Slot %d.*\s+(?P<type>.+)\sPort adapter,\s(?P<port>.+)port(s?).*\
                      Serial number\s+(?P<serial_number>\d+).*" % slot_number
                    match_slot = re.match(regex, slot_results, re.DOTALL)
                    group_slot = match_slot.groupdict()
                    linecard_type = group_slot["type"]
                    port_number = group_slot["port"]
                    serial_number = group_slot["serial_number"]
                    module["type"] = linecard_type, port_number + " port(s)" 
                    module["serial_number"] = serial_number
                    node_diagram["module %d" % slot_number] = module
                return node_diagram
            except AttributeError:
                print "There might be some issue with the 'show diag' output."

def configure():
    """This creates a nice and userfriendly command line."""
    parser = argparse.ArgumentParser(description="welcome to network_inventory!"
        "This is a fancy tool enabling dynamic inventory inside your network. You'll obtain information about "
        "Routers models, IOS Versions, RAM Memory, Total Flash memory and Free Flash memory, Linecards and serial numbers.")
    parser.add_argument('-u', '--username', dest='username',
            help='username to login to nodes')
    parser.add_argument('-p', '--password', dest='password',
            help='password to login to nodes')
    parser.add_argument('-f', '--filename', dest='filename',
            help='text file containing the node data (expected format...)')
    return parser.parse_args()

def read_node_file(filename):
    """ this function reads the node file and returns the content in a
    dictionary format.

    Arguments:
        <filename> string: the file name to read.

    Returns:
        <nodes> dictionary: contains the parsed content of <filename>
            example:
            nodes = {
                "router1": {"ipv4_address": "10.1.1.1", "platform": "CiscoIOS"},
                "router2": {"ipv4_address": "10.1.1.2", "platform": "CiscoIOS"},
            }
    """
    nodes = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                params = {}
                device_list = line.split()
                router = device_list[0]
                ip = device_list[1]
                platform = device_list[2]
                params["ipv4_address"] = ip
                params["platform"] = platform
                nodes[router] = params
    except IOError:
        print "File %s does not exist!" % filename 
    return nodes

def main(args):
    """ main method to run this script, here's where all the magic begins. """
    # getting the missing parameters, if any.
    if not args.username:
        args.username = raw_input("Please enter username: ")
    if not args.password:
        args.password = getpass("Please enter password: ")
    if not args.filename:
        args.filename = raw_input("Please enter filename: ")
    # reading file content.
    nodes = read_node_file(args.filename)
    # getting node information.
    diagram = {}
    errors = []
    for router in nodes:
        if nodes[router].get("ipv4_address") and nodes[router].get("platform"):
            # all the data we need is available, let's start data collection.
            if nodes[router]["platform"] == "CiscoIOS":
                r = IOS_Router(args.username, args.password,
                        nodes[router]["ipv4_address"])
                diagram[router] = r.get_node_info()
        else:
            errors.append("%s error: missing parameters!" % router)

    # prints to results in a pretty format.
    pretty = pprint.PrettyPrinter(indent=2, depth=10).pprint
    if diagram:
        print("\nRESULTS:\n")
        pretty(diagram)
    if errors:
        print("\nERRORS:\n")
        pretty(errors)

if __name__ == '__main__':
    sys.exit(main(configure()))
