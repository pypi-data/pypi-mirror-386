Remote read_sql
===============

Read SQL into a pandas data frame from a remote server

Installation
------------

.. code-block:: bash

    pip install remote-read-sql

Usage
-----

In this example, ``remote_read_sql`` opens an ssh tunnel and connects to the mysql server locally on port 3306. The SQL query is sanitized and passed to ``pandas`` ``read_sql``.

After reading the data into the dataframe, the ssh and db connections are closed.

Storing your credentials in files
+++++++++++++++++++++++++++++++++

You should read your credentials from a file or files. Do not write credentials directly in your notebook.

In this example, the ssh credentials are in a ENV file that might look something like this::

    SSH_SERVER_IP=server.example.com
    SSH_USER=user
    SSH_KEY_PATH=~/.ssh/id_rsa
    SSH_KEY_PASS=
    LOCAL_BIND_PORT=3307
    REMOTE_HOST=127.0.0.1
    LOCAL_BIND_PORT=3307
    REMOTE_DB_PORT=3306

and the mysql credentials are in the ``my.cnf`` file and might look like this::

    [remote_server]
    user=user_readonly
    password=password
    default-character-set=utf8
    host=127.0.0.1
    port=3306

Preparing your credentials
++++++++++++++++++++++++++

Since you may be calling ``remote_read_sql`` several times in the same notebook, store the paths to your credentials in a dictionary as a convenience.

.. code-block:: python

    # change to your own paths
    ssh_config_path = Path("~/.my_ssh_config")
    my_cnf_path = Path("~/.my.cnf")
    db_name = "my_database"

    # combine kwargs into a dictionary
    conn_opts = {
        "ssh_config_path": ssh_config_path,
        "my_cnf_path": my_cnf_path,
        "my_cnf_connection_name": "remote_server",
        "db_name": db_name,
    }

Running a single query
++++++++++++++++++++++

To run a single query and return a Dataframe, pass the SQL query to ``remote_read_sql`` along with your ``conn_opts`` from above. The SQL query must be a valid SELECT query.

.. code-block:: python

    # open ssh, open db, read SQL into dataframe, close db, close ssh
    df = remote_read_sql("SELECT * FROM subject_glucose", **conn_opts)

    # inspect the dataframe
    df.head()


Running multiple queries
++++++++++++++++++++++++

When running ``remote_read_sql`` with the SQL query as above, the connection closes immediately after running the SQL statement. If you want to run several SQL queries using the same connection, use ``remote_connect`` as a context manager.

* ``remote_connect`` opens the connection.
* call ``pd.read_sql()`` for multiple SQL queries within the ``with`` statement
* Once you leave the ``with`` statement, ``remote_connect`` closes the connection.

If you have read/write permissions to your database, you may want to pass your query through ``safe_sql`` before you pass it to pandas ``read_sql``.

.. code-block:: python

    import pandas as pd
    from remote_read_sql import remote_connect, safe_sql

    with remote_connect(**conn_opts) as db_conn:
        # connection db_conn is open
        # read sql
        df_glucose = pd.read_sql(safe_sql("SELECT * FROM subject_glucose"), db_conn)
        # read sql
        df_bp = pd.read_sql(safe_sql("SELECT * FROM subject_bp"), db_conn)

    # connection db_conn is closed
    # view your Dataframes
    df_glucose.head()
    df_bp.head()
