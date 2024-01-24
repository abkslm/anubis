#!/usr/bin/python3 -u

from subprocess import run, getstatusoutput, check_output, CalledProcessError, CompletedProcess
from datetime import datetime
from random import shuffle
from sys import argv, exit

__author__ = "Andrew B. Moore"
__copyright__ = "Copyright 2024, University of San Francisco, Department of Computer Science"
__credits__ = ["Andrew B. Moore"]

__license__ = "None"
__version__ = "1.11.0"
__maintainer__ = "Andrew B. Moore"
__email__ = "support@cs.usfca.edu"
__status__ = "Production"

ALIASES = {"beagle": [1, 5]}


def anubis():
    options = parse_args(argv)
    alias = options["alias"]
    relay_mode = options["relay"]

    if not (options["connect"] or options["status"]):
        fail_usage()

    print_option("\nRunning anubis...", relay_mode)

    if options["connect"]:
        offline: [str] = []

        print_option("\nFinding optimal host for alias: " + alias + "...", relay_mode)

        runs = 1
        suggested_host = ballast_suggest(alias)
        if suggested_host:
            while len(offline) < ALIASES[alias][1] and runs < ALIASES[alias][1] * 2:
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
        random_hosts = random_host_order(ALIASES[alias][0], ALIASES[alias][1])
        while random_hosts:
            print_option("...", relay_mode)
            host = (alias + str(random_hosts.pop()))
            if host not in offline and host_is_alive(host):
                if relay_mode:
                    ssh_relay(host)
                exit(0) if connect(host, options["forward"]) else offline.append(host)
            elif suggested_host not in offline:
                offline.append(host)

        print_option("\n", relay_mode)

        fail("No hosts for alias " + alias + " connectable!\n"
                                             "If this error persists, please contact support@cs.usfca.edu", 2)

    elif options["status"]:
        if alias:
            print_statuses(alias)
        else:
            print("\nGlobal Status:")
            for alias in ALIASES.keys():
                print_statuses(alias)

    exit(0)


def ballast_suggest(alias: str) -> str:
    try:
        return check_output(["/usr/local/bin/ballast", "-l", alias]).decode("utf-8").split('.')[0]
    except CalledProcessError:
        return ""
    except KeyboardInterrupt:
        fail_interrupt("Ballast suggestion")


def random_host_order(start: int, end: int) -> [int]:
    random_list: [int] = list(range(start, end + 1))
    shuffle(random_list)
    return random_list


def host_is_alive(host: str) -> bool:
    try:
        status, _ = getstatusoutput("ping -c 1 -w 1 " + host)
        if status == 0:
            return True
        return False
    except CalledProcessError:
        fail("Could not check if host \"" + host + "\" is alive!", 2)
    except KeyboardInterrupt:
        fail_interrupt("Liveness check")


def ssh_relay(host: str):
    try:
        run(["nc", host, "22"])
    except CalledProcessError:
        fail("Could not form an SSH relay!\n"
             "Please contact support@cs.usfca.edu if this error persists.", 2)
    except KeyboardInterrupt:
        exit(1)


def connect(host: str, forward_agent: bool) -> bool:
    try:
        print("\nConnecting to host: " + host + "...\n")

        completed_process: CompletedProcess[bytes]
        start_time = datetime.now()
        if forward_agent:
            completed_process = run(["ssh", host, "-q", "-o", "ForwardAgent=yes"])
        else:
            completed_process = run(["ssh", host, "-q", "-o", "ConnectTimeout=1"])

        end_time = datetime.now()
        conn_time = (end_time - start_time).total_seconds()
        conn_time_str = ("{:.1f} minutes ({:.2f}s)"
                         .format((conn_time / 60), conn_time)) \
            if conn_time < 36 * 600 else "Way too long :)"

        if completed_process.returncode == 0 or conn_time > 1.0:
            print("\nConnected to " + host + " for: " + conn_time_str)
            print("anubis session ended. Goodbye!\n\n", end='')
            return True

    except CalledProcessError:
        fail("Anubis failed to connect to host: " + host, 2)
    except KeyboardInterrupt:
        fail_interrupt("Connection")


def parse_args(args: [str]) -> {str: str or bool}:
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
                    fail("\n\"--relay\" may only be used in SSH ProxyCommand.\n"
                         "\nPlease use \"ForwardAgent yes\" in SSH config to forward SSH Agent\n"
                         "\tOR\n"
                         "Invoke anubis without --relay (eg \"anubis <alias> --forward\")\n", 2)
                elif "--forward" in args or "-f" in args:
                    parsed["forward"] = True
        else:
            fail_usage()

    elif ("--connect" in args or "-c" in args) and "--status" not in args and "-s" not in args:
        alias_idx: int

        if "--connect" in args:
            alias_idx = args.index("--connect") + 1
        else:
            alias_idx = args.index("-c") + 1

        if len(args) > alias_idx > 1:
            alias = args[alias_idx]
            if alias in ALIASES.keys():
                parsed["alias"] = alias
            else:
                fail("Alias " + alias + " is not valid!", 1)
        else:
            fail("Alias missing! Usage: \"anubis alias\" or \"anubis -c alias\"", 1)

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
        alias_idx: int

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


def print_option(string: str, silent: bool):
    if not silent:
        print(string, end='')


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


def fail_interrupt(process: str):
    fail(process + " interrupted by keyboard (likely ^C), exiting anubis.\n", 1)


def fail(msg: str, code: int):
    print(msg)
    exit(code)


try:
    anubis()
except KeyboardInterrupt:
    print("\n\nExiting anubis...\n"
          "Goodbye!\n")
    exit(0)
except BrokenPipeError:
    fail("Broken pipe! This was likely caused by a keyboard interrupt (^C). Please try again.\n"
         "If this error persists, please contact support@cs.usfca.edu\n", 2)
