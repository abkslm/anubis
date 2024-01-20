import subprocess
import sys

ALIASES = {"beagle": [1, 5]}


def parse_args(args: [str]) -> {}:
    parsed = {"alias": "", "status": True, "connect": False}

    if ("--connect" in args or "-c" in args) and ("--status" not in args and "-s" not in args):
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
            fail("Alias missing! Usage: \"--flag alias\"", 1)

        parsed["status"] = False
        parsed["connect"] = True

    elif ("--status" in args or "-s" in args) and ("--connect" not in args and "-c" not in args):
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

    return parsed


def fail(msg: str, code: int):
    print(msg)
    exit(code)


def host_is_alive(host: str) -> bool:
    try:
        status, _ = subprocess.getstatusoutput("ping -c 1" + host)
        if status == 0:
            return True
        return False
    except subprocess.CalledProcessError:
        fail("Could not check if host \"" + host + "\" is alive!", 2)


def ballast_suggest(alias: str) -> str:
    print("Requesting host for " + alias + "...")
    try:
        return subprocess.check_output(["/usr/local/bin/ballast", "-l", alias]).decode("utf-8")
    except subprocess.CalledProcessError:
        fail("""
        Ballast failed to suggest a host!
        Please contact support@cs.usfca.edu if this error persists.
        """, 2)


def connect(host: str):
    try:
        print("Connecting to host: " + host + "...")
        subprocess.run(["ssh", host])
        # print("Connected to host: " + host + "!")
    except subprocess.CalledProcessError:
        fail("Anubis failed to connect to the Ballast-suggested host!", 2)


def anubis():

    print("Running Anubis...")

    parsed = parse_args(sys.argv)

    alias = parsed["alias"]

    if parsed["connect"]:
        offline = [str]
        connected = False
        suggested_host = ballast_suggest(alias)
        while not connected and len(offline) < ALIASES[alias][1]:
            if suggested_host not in offline and host_is_alive(suggested_host):
                connect(suggested_host)
                connected = True
                # break
            else:
                offline.append(suggested_host)
                suggested_host = ballast_suggest(alias)

    elif parsed["status"]:
        if alias:
            start_id = ALIASES[alias][0]
            end_id = ALIASES[alias][1]

            host = alias + str(start_id)
            if host_is_alive(host):
                print("\n" + host + ": online\n", end='')
            else:
                print("\n" + host + ": offline\n", end='')

            start_id += 1

            for i in range(start_id, end_id + 1):
                host = alias + str(i)
                if host_is_alive(host):
                    print(host + ": online\n", end='')
                else:
                    print(host + ": offline\n", end='')
        else:
            for alias in ALIASES.keys():

                print("\nStatus for nodes in alias " + alias + ":\n", end='')

                start_id = ALIASES[alias][0]
                end_id = ALIASES[alias][1]

                for i in range(start_id, end_id + 1):
                    host = alias + str(i)
                    if host_is_alive(host):
                        print(host + ": online\n", end='')
                    else:
                        print(host + ": offline\n", end='')
                print()


anubis()
