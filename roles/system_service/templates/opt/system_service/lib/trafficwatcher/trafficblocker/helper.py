import re
import subprocess
import logging
from datetime import datetime
import sys
import time

from smartserver import command

class Helper():
    @staticmethod
    def _fetchBlockedIps(result, cmd, regex):
        returncode, cmd_result = command.exec2(cmd)
        if returncode != 0:
            raise Exception("Cmd '{}' was not successful".format(" ".join(cmd)))

        for row in cmd_result.split("\n"):
            if "trafficblocker" not in row:
                continue
            match = re.match("-A SMARTSERVER_BLOCKER -s {} .* -j DROP".format(regex) ,row)
            if match:
                result.append(match[1])

    @staticmethod
    def getBlockedIps(config):
        result = []
        if config.nftables_enabled:
            Helper._fetchBlockedIps(result, ["/usr/sbin/nft", "list", "chain", "inet", "filter", "SMARTSERVER_BLOCKER"], r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})/32")
        else:
            Helper._fetchBlockedIps(result, ["/sbin/iptables-legacy", "-S", "SMARTSERVER_BLOCKER"], r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})/32")
            Helper._fetchBlockedIps(result, ["/sbin/ip6tables-legacy", "-S", "SMARTSERVER_BLOCKER"], r"([0-9a-z:]*)/128")
        return result

    @staticmethod
    def _modifyBlockedIps(cmd):
        returncode, cmd_result = command.exec2(cmd)
        if returncode != 0:
            raise Exception("Cmd '{}' was not successful".format(" ".join(cmd)))

    @staticmethod
    def blockIp(config, ip):
        if config.nftables_enabled:
            ip = "{}/128".format(ip) if ":" in ip else "{}/32".format(ip)
            cmd = ["/usr/sbin/nft", "add", "rule", "inet", "filter", "SMARTSERVER_BLOCKER", "ip saddr", ip, "drop", "comment", "'trafficblocker'"]
        else:
            if ":" in ip:
                cmd = ["/sbin/ip6tables-legacy", "-I", "SMARTSERVER_BLOCKER", "-s", "{}/128".format(ip), "-m", "comment", "--comment", "trafficblocker", "-j", "DROP"]
            else:
                cmd = ["/sbin/iptables-legacy", "-I", "SMARTSERVER_BLOCKER", "-s", "{}/32".format(ip), "-m", "comment", "--comment", "trafficblocker", "-j", "DROP"]
        Helper._modifyBlockedIps(cmd)

    @staticmethod
    def unblockIp(config, ip):
        if config.nftables_enabled:
            ip = "{}/128".format(ip) if ":" in ip else "{}/32".format(ip)
            cmd = ["/usr/sbin/nft", "delete", "rule", "inet", "filter", "SMARTSERVER_BLOCKER", "ip saddr", ip, "drop", "comment", "'trafficblocker'"]
        else:
            if ":" in ip:
                cmd = ["/sbin/ip6tables-legacy", "-D", "SMARTSERVER_BLOCKER", "-s", "{}/128".format(ip), "-m", "comment", "--comment", "trafficblocker", "-j", "DROP"]
            else:
                cmd = ["/sbin/iptables-legacy", "-D", "SMARTSERVER_BLOCKER", "-s", "{}/32".format(ip), "-m", "comment", "--comment", "trafficblocker", "-j", "DROP"]
        Helper._modifyBlockedIps(cmd)
