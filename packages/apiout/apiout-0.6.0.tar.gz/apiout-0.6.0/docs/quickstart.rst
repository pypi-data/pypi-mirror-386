Quickstart Guide
================

This guide will help you get started with **apiout** in minutes.

Installation
------------

Install apiout using pip:

.. code-block:: bash

   pip install apiout

Basic Usage
-----------

1. Without Serializers (Auto-serialize)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a file ``apis.toml``:

.. code-block:: toml

   [[apis]]
   name = "berlin_weather"
   module = "openmeteo_requests"
   client_class = "Client"
   method = "weather_api"
   url = "https://api.open-meteo.com/v1/forecast"

   [apis.params]
   latitude = 52.52
   longitude = 13.41
   current = ["temperature_2m"]

Run the fetcher:

.. code-block:: bash

   apiout run --config apis.toml --json

The tool will automatically convert response objects to dictionaries.

2. With Inline Serializers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add serializer configuration to the same file:

.. code-block:: toml

   [serializers.openmeteo]
   [serializers.openmeteo.fields]
   latitude = "Latitude"
   longitude = "Longitude"

   [serializers.openmeteo.fields.current]
   method = "Current"
   [serializers.openmeteo.fields.current.fields]
   time = "Time"

   [[apis]]
   name = "berlin_weather"
   module = "openmeteo_requests"
   client_class = "Client"
   method = "weather_api"
   url = "https://api.open-meteo.com/v1/forecast"
   serializer = "openmeteo"

   [apis.params]
   latitude = 52.52
   longitude = 13.41
   current = ["temperature_2m"]

Run the same command:

.. code-block:: bash

   apiout run --config apis.toml --json

3. With Separate Serializer File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create ``apis.toml``:

.. code-block:: toml

   [[apis]]
   name = "berlin_weather"
   module = "openmeteo_requests"
   client_class = "Client"
   method = "weather_api"
   url = "https://api.open-meteo.com/v1/forecast"
   serializer = "openmeteo"

   [apis.params]
   latitude = 52.52
   longitude = 13.41
   current = ["temperature_2m"]

Create ``serializers.toml``:

.. code-block:: toml

   [serializers.openmeteo]
   [serializers.openmeteo.fields]
   latitude = "Latitude"
   longitude = "Longitude"

   [serializers.openmeteo.fields.current]
   method = "Current"
   [serializers.openmeteo.fields.current.fields]
   time = "Time"

Run with both files:

.. code-block:: bash

   apiout run --config apis.toml --serializers serializers.toml --json

4. With Reusable Client Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When multiple APIs use the same client, define it once and reference it:

.. code-block:: toml

   [clients.mempool]
   module = "pymempool"
   client_class = "MempoolAPI"
   init_params = {api_base_url = "https://mempool.space/api/"}

   [[apis]]
   name = "block_tip_hash"
   client = "mempool"
   method = "get_block_tip_hash"

   [[apis]]
   name = "block_tip_height"
   client = "mempool"
   method = "get_block_tip_height"

   [[apis]]
   name = "recommended_fees"
   client = "mempool"
   method = "get_recommended_fees"

Run the command:

.. code-block:: bash

   apiout run --config apis.toml --json

This eliminates repetition when multiple APIs share the same client configuration.

5. With JSON Input
~~~~~~~~~~~~~~~~~~

You can provide configuration as JSON via stdin instead of TOML files:

.. code-block:: bash

   echo '{
     "apis": [{
       "name": "berlin_weather",
       "module": "openmeteo_requests",
       "client_class": "Client",
       "method": "weather_api",
       "url": "https://api.open-meteo.com/v1/forecast",
       "params": {
         "latitude": 52.52,
         "longitude": 13.41,
         "current": ["temperature_2m"]
       }
     }]
   }' | apiout run --json

Or convert TOML to JSON using ``taplo``:

.. code-block:: bash

   taplo get -f apis.toml -o json | apiout run --json

CLI Commands
------------

run
~~~

Fetch API data with configuration:

.. code-block:: bash

   apiout run --config <config.toml> [--serializers <serializers.toml>] [--json]
   <json-source> | apiout run [--json]  # Read JSON config from stdin

**Options:**

* ``-c, --config``: Config file to load (can be specified multiple times). Accepts:
  - Config name (e.g., ``mempool``) → loads from ``~/.config/apiout/mempool.toml``
  - File path (e.g., ``./local.toml`` or ``/abs/path/config.toml``)
* ``-s, --serializers``: Serializer file to load (can be specified multiple times). Accepts:
  - Serializer name (e.g., ``my_serializers``) → loads from ``~/.config/apiout/my_serializers.toml``
  - File path (e.g., ``./serializers.toml`` or ``/abs/path/serializers.toml``)
* ``-p, --param``: Method parameter in format ``key=value`` (can be specified multiple times)
* ``--json``: Output as JSON format (default: pretty-printed)

When piping JSON to stdin (without ``-c``), apiout automatically detects and parses it.

generate
~~~~~~~~

Generate serializer configuration by introspecting an API:

.. code-block:: bash

   apiout generate \
     --module openmeteo_requests \
     --client-class Client \
     --method weather_api \
     --url "https://api.open-meteo.com/v1/forecast" \
     --params '{"latitude": 52.52, "longitude": 13.41, "current": ["temperature_2m"]}' \
     --name openmeteo

**Options:**

* ``-m, --module``: Python module name (required)
* ``-c, --client-class``: Client class name (default: "Client")
* ``--method``: Method name to call (required)
* ``-u, --url``: API URL (required)
* ``-p, --params``: JSON params dict (default: "{}")
* ``-n, --name``: Serializer name (default: "generated")

Next Steps
----------

* Read the :doc:`user_guide` for detailed information on configuration options
* Check out :doc:`examples` for more complex use cases
* Explore the :doc:`api_reference` for programmatic usage
