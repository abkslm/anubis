# anubis
anubis is an extension of NASA's [Ballast](https://github.com/pkolano/ballast),
built to better handle offline hosts. By stock behavior, Ballast has a three-minute delay
between liveness checks; while Ballast can be configured to determine an agent has gone offline
after a shorter period of time, this may erroneously mark agents as offline if they happen to check
in after the cutoff.

## Installation:

- Modify the `ALIASES` dictionary `anubis.py` to contain hosts and their range.
  For example, if a Ballast alias `alias` exists, and hostnames are within range
  `[1-5]` (eg `alias1`, `alias2` ... `alias5`), the proper entry would be:
  `"alias":[1,5]`.
- Install `anubis.py` to the system PATH.
  - For example: `install -m 755 -o root anubis.py /usr/local/bin/anubis.py`
- Create a shell alias from `python3 anubis.py` to `anubis`
  - For example: `alias anubis="python3 /usr/local/bin/anubis.py"`
- Ensure `anubis.py` is owned by root, world-readable and world-executable, root-writable (the `install` command
  mentioned earlier handles this automatically)
  - `chown anubis.py root`
  - `chmod 755 anubis.py`

## Usage:
- `anubis --connect alias`
  - `anubis --connect some-host-alias`


- `anubis --status (alias)`
  - `anubis --status`
  - `anubis --status some-host-alias`