#!/usr/bin/python3 -u

import subprocess
import sys

ALIASES = {"beagle": [1, 5]}


def parse_args(args: [str]) -> {}:
    parsed = {"alias": "", "status": False, "connect": False, "last": False}

    if not ("--connect" in args or "-c" in args or "--status" in args or "-s" in args):
        if len(args) > 1:
            alias = args[1]
            if alias in ALIASES.keys():
                parsed["alias"] = alias
                parsed["connect"] = True
                if "--last" in args or "-l" in args:
                    parsed["last"] = True
        else:
            fail_usage()

    elif ("--connect" in args or "-c" in args) and ("--status" not in args and "-s" not in args):
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
            fail("Alias missing! Usage: \"alias\" or \"--flag alias\"", 1)

        if "--last" in args or "-l" in args:
            parsed["last"] = True

        parsed["status"] = False
        parsed["connect"] = True

    elif ("--status" in args or "-s" in args) and "--connect" not in args and "-c" not in args:
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


def fail(msg: str, code: int):
    print(msg, flush=True)
    sys.exit(code)


def fail_usage():
    fail("\nIncorrect Usage!\n"
         "\nUsage:\n"
         "\n\tan \"<alias>\" is a system group name, for example: \"beagle\"\n\n"
         "\t\"anubis <alias>\" or \"anubis -c <alias>\" (or --connect) to connect\n"
         "\t\"anubis -s (or --status) <alias>\" for alias status\n"
         "\t\"anubis -s (or --status)\" for global status\n"
         "\n\t\"anb\" can be used in place of \"anubis\"\n", 1)


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
        fail("""
        Ballast failed to suggest a host!
        Please contact support@cs.usfca.edu if this error persists.
        """, 2)


def connect(host: str):
    try:
        print("\nConnecting to host: " + host + "...\n")
        subprocess.run(["ssh", host])
    except subprocess.CalledProcessError:
        fail("Anubis failed to connect to the Ballast-suggested host!", 2)


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
    parsed = parse_args(sys.argv)

    alias = parsed["alias"]

    print("Running anubis...")

    if parsed["connect"]:
        offline = [str]
        connected = False
        if parsed["last"]:
            print("\nAttempting connection to last " + alias + " host", end='')
            connect(alias + "-last")
        else:
            print("\nFinding optimal host for alias " + alias + "...", end='')
            runs = 0
            suggested_host = ballast_suggest(alias)
            while not connected and len(offline) < ALIASES[alias][1] and runs < ALIASES[alias][1] * 2:
                print("...", end='')
                if suggested_host not in offline and host_is_alive(suggested_host):
                    connect(suggested_host)
                    connected = True
                elif suggested_host not in offline:
                    offline.append(suggested_host)
                suggested_host = ballast_suggest(alias)
                runs += 1
            if not connected:
                fail("No hosts for alias " + alias + " online!"
                                                     "If this error persists, please contact support@cs.usfca.edu", 1)
            print()

    elif parsed["status"]:
        if alias:
            print_statuses(alias)
        else:
            print("\nGlobal Status:")
            for alias in ALIASES.keys():
                print_statuses(alias)


try:
    anubis()
except KeyboardInterrupt:
    print("\n\nKeyboardInterrupt Detected, exiting anubis.\n"
          "Goodbye!\n")
