#!/usr/bin/python3 -u

from datetime import datetime
from random import randint
import subprocess
import sys

ALIASES = {"beagle": [1, 5]}


def print_option(string: str, silent: bool):
    if not silent:
        print(string, end='')


def fail(msg: str, code: int):
    print(msg)
    sys.exit(code)


def fail_usage():
    fail("\nIncorrect Usage!\n"
         "\nUsage:\n"
         "\n\tan \"<alias>\" is a system group name, for example: \"beagle\"\n\n"
         "\t\"anubis <alias>\" or \"anubis -c (or --connect) <alias>\" to connect\n"
         "\t\"anubis -c <alias> --forward\" or \"anubis <alias> -f\" to forward SSH Agent\n"
         "\t\"anubis -s (or --status) <alias>\" for alias status\n"
         "\t\"anubis -s (or --status)\" for global status\n"
         "\n\t\"anb\" can be used in place of \"anubis\"\n"
         "\n\tFor example (connect to alias \"beagle\" and forward SSH Agent):\n"
         "\t\t\"anb beagle -f\" or \"anubis --connect beagle --forward\"\n", 1)


def parse_args(args: [str]) -> {}:
    parsed = {"alias": "", "status": False, "connect": False, "relay": False, "forward": False}

    if not ("--connect" in args or "-c" in args or "--status" in args or "-s" in args):
        if len(args) > 1:
            alias = args[1]
            if alias in ALIASES.keys():
                parsed["alias"] = alias
                parsed["connect"] = True
                if "--relay" in args and ("--forward" not in args and "-f" not in args):
                    parsed["relay"] = True
                elif "--relay" in args and ("--forward" in args or "-f" in args):
                    fail("--relay may only be used in SSH ProxyCommand.\n"
                         "Please use \"ForwardAgent yes\" in SSH invocation to forward SSH Agent.", 2)
                elif "--forward" in args or "-f" in args:
                    parsed["forward"] = True
        else:
            fail_usage()

    elif ("--connect" in args or "-c" in args) and "--status" not in args and "-s" not in args:
        alias_idx = -1

        if "--connect" in args:
            alias_idx = args.index("--connect") + 1
        elif "-c" in args:
            alias_idx = args.index("-c") + 1

        if len(args) > alias_idx > 1:
            alias = args[alias_idx]
            if alias in ALIASES.keys():
                parsed["alias"] = alias
            else:
                fail("Alias " + alias + " is not valid!", 1)
        else:
            fail("Alias missing! Usage: \"alias\" or \"-c alias\"", 1)

        if "--relay" in args:
            parsed["relay"] = True
        elif "--relay" in args and ("--forward" in args or "-f" in args):
            fail("--relay may only be used in SSH ProxyCommand.\n"
                 "Please use \"ForwardAgent yes\" in SSH invocation to forward SSH Agent.", 2)
        else:

            if "--forward" in args or "-f" in args:
                parsed["forward"] = True

        parsed["status"] = False
        parsed["connect"] = True

    elif (("--status" in args or "-s" in args)
          and "--connect" not in args and "-c" not in args
          and "--relay" not in args):
        alias_idx: -1

        if "--status" in args:
            alias_idx = args.index("--status") + 1
        else:
            alias_idx = args.index("-s") + 1

        if len(args) > alias_idx > 1:
            alias = args[alias_idx]
            if alias in ALIASES.keys():
                parsed["alias"] = alias
            else:
                fail("Alias " + alias + " is not valid!", 1)
        parsed["status"] = True

    else:
        fail_usage()

    return parsed


def host_is_alive(host: str) -> bool:
    try:
        status, _ = subprocess.getstatusoutput("ping -c 1 -w 1 " + host)
        if status == 0:
            return True
        return False
    except subprocess.CalledProcessError:
        fail("Could not check if host \"" + host + "\" is alive!", 2)


def ballast_suggest(alias: str) -> str:
    try:
        return subprocess.check_output(["/usr/local/bin/ballast", "-l", alias]).decode("utf-8").split('.')[0]
    except subprocess.CalledProcessError:
        return ""


def random_host_order(start: int, end: int):
    initial_set: [int] = []
    for i in range(start, end + 1):
        initial_set.append(i)

    random_set: [int] = []
    while len(initial_set) > 0:
        random_set.append(
            str(
                initial_set.pop(
                    randint(0, len(initial_set) - 1)
                )
            )
        )

    return random_set


def ssh_relay(host: str):
    subprocess.run(["nc", host, "22"])


def connect(host: str, forward_agent: bool):
    try:
        print("\nConnecting to host: " + host + "...\n")

        completed_process: subprocess.CompletedProcess[bytes]
        start_time = datetime.now()
        if forward_agent:
            completed_process = subprocess.run(["ssh", host, "-q", "-o", "ForwardAgent=yes"])
        else:
            completed_process = subprocess.run(["ssh", host, "-q", "-o", "ConnectTimeout=1"])

        end_time = datetime.now()
        conn_time = (end_time - start_time).total_seconds()
        conn_time_str = ("{:.1f} minutes ({:.2f}s)"
                         .format((conn_time / 60), conn_time)) \
            if conn_time < 36 * 600 else "Way too long :)"

        if completed_process.returncode == 0 or conn_time > 1.0:
            print("\nConnected to " + host + " for: " + conn_time_str)
            print("anubis session ended. Goodbye!\n\n", end='')
            return True

    except subprocess.CalledProcessError:
        fail("Anubis failed to connect to host: " + host, 2)


def print_statuses(alias: str):
    print("\nStatus for nodes in alias " + alias + ":")

    start_id = ALIASES[alias][0]
    end_id = ALIASES[alias][1]

    statuses = {}

    print("Pinging...", end='')

    for i in range(start_id, end_id + 1):
        host = alias + str(i)
        if host_is_alive(host):
            statuses[host] = True
        else:
            statuses[host] = False
        print("...", end='')
    print("Done.\n")

    for host in statuses.keys():
        if statuses[host]:
            print(str(host) + ": ✅ online\n", end='')
        else:
            print(str(host) + ": ❌ offline\n", end='')
    print()


def anubis():
    options = parse_args(sys.argv)
    alias = options["alias"]
    relay_mode = options["relay"]

    if not (options["connect"] or options["status"]):
        fail_usage()

    print_option("\nRunning anubis...", relay_mode)

    if options["connect"]:
        connected = False
        offline: [str] = []

        print_option("\nFinding optimal host for alias: " + alias + "...", relay_mode)

        runs = 1
        suggested_host = ballast_suggest(alias)
        if suggested_host:
            while not connected and len(offline) < ALIASES[alias][1] and runs < ALIASES[alias][1] * 2:
                print_option("...", relay_mode)
                if suggested_host not in offline and host_is_alive(suggested_host):
                    if relay_mode:
                        ssh_relay(suggested_host)
                    exit(0) if connect(suggested_host, options["forward"]) else offline.append(suggested_host)
                elif suggested_host not in offline:
                    offline.append(suggested_host)
                suggested_host = ballast_suggest(alias)
                if not suggested_host:
                    break
                runs += 1

        print_option("\n", relay_mode)

        print_option("Ballast offline! Picking a host at random...", relay_mode)
        random_host_set = random_host_order(ALIASES[alias][0], ALIASES[alias][1])
        while not connected and random_host_set:
            print_option("...", relay_mode)
            host = (alias + random_host_set.pop())
            if host not in offline and host_is_alive(host):
                if relay_mode:
                    ssh_relay(host)
                else:
                    exit(0) if connect(host, options["forward"]) else offline.append(host)
            else:
                offline.append(host)
        print_option("\n", relay_mode)

        if not connected:
            fail("No hosts for alias " + alias + " connectable!\n"
                                                 "If this error persists, please contact support@cs.usfca.edu", 1)
        print_option("\n", relay_mode)

    elif options["status"]:
        if alias:
            print_statuses(alias)
        else:
            print("\nGlobal Status:")
            for alias in ALIASES.keys():
                print_statuses(alias)


try:
    anubis()
except KeyboardInterrupt:
    print("\n\nExiting anubis...\n"
          "Goodbye!\n")
