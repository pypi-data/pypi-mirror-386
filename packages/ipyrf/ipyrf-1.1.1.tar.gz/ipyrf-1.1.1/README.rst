ipyrf
=====

Minimal iperf3-like network throughput tool with JSON output. Supports TCP and UDP, server and client modes.

Features
--------
- TCP and UDP tests
- JSON or human-readable output
- Optional bandwidth capping (TCP/UDP)
- UDP packet loss estimation
- Linux TCP congestion control selection (if available)

Installation
------------

From PyPI (recommended):

.. code-block:: bash

   python3 -m pip install ipyrf

From source (editable):

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate
   python3 -m pip install -U pip build
   python3 -m pip install -e .

Test Utilities (ipyrf.test)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``ipyrf.test`` module provides test utilities for writing your own tests:

.. code-block:: python

   from ipyrf.test import IPyrfBuilder, CheckCriteria

   def test_my_network(testdirectory):
       builder = IPyrfBuilder(testdirectory)
       port = 12345

       server = builder.build()
       client = builder.build()

       server.run_tcp_server("127.0.0.1", port)
       client.run_tcp_client("127.0.0.1", port, duration=2)

       # Check with custom criteria
       builder.check(
           (server, client),
           timeout=5,
           criteria={"min_bps": 1000000}
       )

Available classes and functions:

- ``IPyrfClient``: Run and monitor ipyrf instances
- ``IPyrfBuilder``: Builder pattern for creating test instances
- ``CheckCriteria``: Configurable criteria for evaluating test results

See ``examples/using_test_utilities.py`` for more examples.

Running Tests
~~~~~~~~~~~~~

The project includes a comprehensive test suite using pytest:

.. code-block:: bash

   # Run all tests
   python3 waf --run_tests

Usage
-----

The package installs a console script named ``ipyrf``.

Quick examples
~~~~~~~~~~~~~~

TCP server:

.. code-block:: bash

   ipyrf tcp server 0.0.0.0 --port 12345

TCP client:

.. code-block:: bash

   ipyrf tcp client 127.0.0.1 --port 12345 --time 5
   ipyrf tcp client 127.0.0.1 --port 12345 --time 5 --set-mss 1400

UDP server:

.. code-block:: bash

   ipyrf udp server 0.0.0.0 --port 12345

UDP client (with bandwidth cap and optional payload size):

.. code-block:: bash

   ipyrf udp client 127.0.0.1 --port 12345 --bandwidth 50M --time 5
   ipyrf udp client 127.0.0.1 --port 12345 --bandwidth 50M --time 5 -l 1200

Interactive mode
----------------

You can run clients in an interactive mode that lets you adjust the pacing live using your keyboard. Use ``--interactive`` and optionally ``--interval`` (seconds between stats updates). When interactive is enabled, the same client logic is used underneath with a dynamic pacing controller.

Controls shown in the terminal:

- ``←``: -1 Mbps
- ``→``: +1 Mbps
- ``↓``: -10%
- ``↑``: +10%
- ``0``: reset to initial bandwidth (or unlimited for TCP if none was provided)
- ``u``: unlimited (disable pacing)
- ``q``: quit

Examples:

.. code-block:: bash

   # TCP interactive (unlimited unless you pass --bandwidth)
   ipyrf tcp client 127.0.0.1 --port 5201 --interactive

   # TCP interactive with initial pacing and custom interval
   ipyrf tcp client 127.0.0.1 --port 5201 --bandwidth 200M --set-mss 1400 --interactive --interval 0.5

   # UDP interactive (requires initial --bandwidth)
   ipyrf udp client 127.0.0.1 --port 5201 --bandwidth 50M -l 1200 --interactive

CLI overview
------------

Top-level structure:

.. code-block:: text

   ipyrf [tcp|udp] [server|client] [OPTIONS]

Common options (both protocols, both roles):

- ``--port``: Port (default 5201)
- ``--logfile``: Redirect output to a file
- ``--json_log``: Emit logs in JSON (newline-delimited)

TCP-specific options:

- ``tcp server ADDRESS``: Start a TCP server on ``ADDRESS``
- ``tcp client ADDRESS``: Start a TCP client to connect to ``ADDRESS``
- ``--congestion-control``: Select Linux TCP CC algorithm if available
- ``--time``: Test duration (seconds), default 10
- ``--bandwidth``: Target rate (e.g., ``50M``); used for pacing, optional
- ``--set-mss``: Set approximate MSS via ``TCP_MAXSEG``
- ``--interactive``: Enable interactive pacing controls
- ``--interval``: Stats interval in seconds for interactive mode (default 1.0)

UDP-specific options:

- ``udp server ADDRESS``: Start a UDP server on ``ADDRESS``
- ``udp client ADDRESS``: Start a UDP client to ``ADDRESS``
- ``--time``: Test duration (seconds), default 10
- ``--bandwidth``: Target rate (required for UDP client; e.g., ``50M``)
- ``-l/--length``: UDP payload length (default 1200)
- ``--interactive``: Enable interactive pacing controls
- ``--interval``: Stats interval in seconds for interactive mode (default 1.0)

JSON logging
------------

Add ``--json_log`` to switch all output to newline-delimited JSON objects. This is useful for machine parsing or dashboards. Example:

.. code-block:: bash

   ipyrf tcp client 127.0.0.1 --time 5 --json_log | jq

Notes
-----

- Output is JSON (newline-delimited for update events) when ``--json_log`` is given; otherwise, a human-readable summary is printed.
- UDP mode sends a FIN marker at the end and the server exits after FIN (or inactivity timeout).
- On Linux, congestion control selection is exposed if ``/proc`` entries are available.

License
-------

MIT. See ``LICENSE``.
