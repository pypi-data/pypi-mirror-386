Configuration
=============

Scaler comes with a number of settings that can be tuned for performance. Reasonable defaults are chosen for these that will yield decent performance, but users can tune these settings to get the best performance for their use case. A full list of the available settings can be found by calling the CLI with the ``-h`` flag.

Object storage server settings
------------------------------

For the list of available settings, use the CLI command:

.. code:: bash

    scaler_object_storage_server -h


Scheduler Settings
------------------

For the list of available settings, use the CLI command:

.. code:: bash

    scaler_scheduler -h

**Protected Mode**

.. _protected:

The Scheduler is started in protected mode by default, which means that it can not be shut down by the Client. This is because multiple Clients can connect to a long-running Scheduler, and calling :py:func:`~Client.shutdown()` may inadverdently kill work that another user is executing. This is also because Scaler encourages strong decoupling between Client, Scheduler, and Workers. To turn off protected mode, start the scheduler with:

.. code:: bash

    scaler_scheduler tcp://127.0.0.1:8516 -p False

Or if using the programmatic API, pass ``protected=False``:

.. code:: python

    from scaler import SchedulerClusterCombo

    cluster = SchedulerClusterCombo(
        address=f"tcp://127.0.0.1:{port}",
        n_workers=2,
        protected=False, # this will turn off protected mode
    )

**Event Loop**

Scaler uses Python's built-in ``asyncio`` event loop by default, however users can choose to use ``uvloop`` for the event loop. ``uvloop`` is a faster implementation of the event loop and may improve performance of Scaler.

``uvloop`` needs to be installed separately:

.. code:: bash

    pip install uvloop

``uvloop`` can be set when starting the scheduler through the CLI:

.. code:: bash

    scaler_scheduler tcp://127.0.0.1:8516 -e uvloop

.. code:: python

    from scaler import SchedulerClusterCombo

    cluster = SchedulerClusterCombo(
        address=f"tcp://127.0.0.1:{port}",
        n_workers=2,
        event_loop="uvloop"
    )


Worker Settings
---------------

For the list of available settings, use the CLI command:

.. code:: bash

    scaler_cluster -h

**Preload Hook**

Workers can execute an optional initialization function before processing tasks using the ``--preload`` option. This enables workers to:

* Set up environments on demand
* Preload data, libraries, or models  
* Initialize connections or state

The preload specification follows the format ``module.path:function(args, kwargs)`` where:

* ``module.path`` is the Python module to import
* ``function`` is the callable to execute
* ``args`` and ``kwargs`` are literal values (strings, numbers, booleans, lists, dicts)

.. code:: bash

    # Simple function call with no arguments
    scaler_cluster tcp://127.0.0.1:8516 --preload "mypackage.init:setup"
    
    # Function call with arguments
    scaler_cluster tcp://127.0.0.1:8516 --preload "mypackage.init:configure('production', debug=False)"

The preload function is executed once per processor during initialization, before any tasks are processed. If the preload function fails, the error is logged and the processor will terminate.

Example preload module (``mypackage/init.py``):

.. code:: python

    import logging
    
    def setup():
        """Basic setup with no arguments"""
        logging.info("Worker initialized")
    
    def configure(environment, debug=True):
        """Setup with configuration parameters"""
        logging.info(f"Configuring for {environment}, debug={debug}")
        # Initialize connections, load models, etc.

**Death Timeout**

Workers are spun up with a ``death_timeout_seconds``, which indicates how long the worker will stay alive without being connected to a Scheduler. The default setting is 300 seconds. This is intended for the workers to clean up if the Scheduler crashes.

This can be set using the CLI:

.. code:: bash

    scaler_cluster -n 10 tcp://127.0.0.1:8516 -ds 300

Or through the programmatic API:



Configuring with TOML Files
---------------------------

While all Scaler components can be configured using command-line flags, using TOML files is the recommended approach for production or shareable setups. Configuration files make your setup explicit, easier to manage, and allow you to check your infrastructure's configuration into version control.

For convenience, you can define the settings for all components in a single, sectioned TOML file. Each component automatically loads its configuration from its corresponding section.

Core Concepts
~~~~~~~~~~~~~

* **Usage**: To use a configuration file, pass its path via the ``--config`` or ``-c`` flag.

    .. code-block:: bash

        scaler_scheduler --config /path/to/your/example_config.toml

* **Precedence**: Settings are loaded in a specific order, with later sources overriding earlier ones. The hierarchy is:

    Command-Line Flags > TOML File Settings > Built-in Default Values

* **Naming Convention**: The keys in the TOML file must match the long-form command-line arguments. The rule is to replace any hyphens (``-``) with underscores (``_``).

    * For example, the flag ``--num-of-workers`` becomes the TOML key ``num_of_workers``.
    * One can discover all available keys by running any command with the ``-h`` or ``--help`` flag.

Supported Components and Section Names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following table maps each Scaler command to its corresponding section name in the TOML file.

.. list-table:: TOML Section Names
   :widths: 50 50
   :header-rows: 1

   * - Command
     - TOML Section Name
   * - ``scaler_scheduler``
     - ``[scheduler]``
   * - ``scaler_cluster``
     - ``[cluster]``
   * - ``scaler_object_storage_server``
     - ``[object_storage_server]``
   * - ``scaler_ui``
     - ``[webui]``
   * - ``scaler_top``
     - ``[top]``
   * - ``scaler_worker_adapter_native``
     - ``[native_worker_adapter]``
   * - ``scaler_worker_adapter_symphony``
     - ``[symphony_worker_adapter]``


Practical Scenarios & Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Scenario 1: Unified Configuration File**

Here is an example of a single ``example_config.toml`` file that configures multiple components using sections.

**example_config.toml**

.. code-block:: toml

    # This is a unified configuration file for all Scaler components.

    [scheduler]
    scheduler_address = "tcp://127.0.0.1:6378"
    object_storage_address = "tcp://127.0.0.1:6379"
    monitor_address = "tcp://127.0.0.1:6380"
    allocate_policy = "even"
    logging_level = "INFO"
    logging_paths = ["/dev/stdout", "/var/log/scaler/scheduler.log"]

    [cluster]
    scheduler_address = "tcp://127.0.0.1:6378"
    num_of_workers = 8
    per_worker_capabilities = "linux,cpu=8"
    task_timeout_seconds = 600

    [object_storage_server]
    object_storage_address = "tcp://127.0.0.1:6379"

    [webui]
    monitor_address = "tcp://127.0.0.1:6380"
    web_port = 8081


With this single file, starting your entire stack is simple and consistent:

.. code-block:: bash

    scaler_object_storage_server --config example_config.toml &
    scaler_scheduler --config example_config.toml &
    scaler_cluster --config example_config.toml &
    scaler_ui --config example_config.toml &


**Scenario 2: Overriding a Section's Setting**

You can override any value from the TOML file by providing it as a command-line flag. For example, to use the ``example_config.toml`` file but test the cluster with 12 workers instead of 8:

.. code-block:: bash

    # The --num-of-workers flag will take precedence over the [cluster] section
    scaler_cluster --config example_config.toml --num-of-workers 12

The cluster will start with **12 workers**, but all other settings (like ``scheduler_address``) will still be loaded from the ``[cluster]`` section of ``example_config.toml``.
