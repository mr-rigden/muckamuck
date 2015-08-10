Install
=============================

System
----------------------------------

.. code-block:: bash

   $ sudo apt-get update
   $ sudo apt-get install build-essential libffi-dev python-dev git
   $ sudo apt-get install libmariadbclient-dev libssl-dev

Download
----------------------------------

.. code-block:: bash

   $ git clone https://github.com/jrigden/muckamuck.git

Redis
----------------------------------

* Install Redis: http://redis.io/topics/quickstart If you have missing LSB tags and overrides see https://github.com/antirez/redis/issues/804 and use $ use sudo utils/install_server.sh

MariaDB
----------------------------------

* Install MariaDB: https://downloads.mariadb.org/mariadb/repositories

.. code-block:: bash

   root $ mysql -u root -p

.. code-block:: sql

    CREATE DATABASE database_name;
    CREATE USER 'username'@'%' IDENTIFIED BY 'password';
    GRANT ALL PRIVILEGES ON database_name.* to 'username'@'%' IDENTIFIED BY 'password';
    FLUSH PRIVILEGES;

Nginx with pagespeed
----------------------------------

1. Build nginx with ngx_pagespeed: https://developers.google.com/speed/pagespeed/module/build_ngx_pagespeed_from_source
2. Need nginx config file

Python
----------------------------------

1. Install Python pip: https://pip.pypa.io/en/latest/installing.html
2. Install Python virtualenv: https://virtualenv.pypa.io/en/latest/installation.html
3. Install Python virtualenvwrapper: https://virtualenvwrapper.readthedocs.org/en/latest/

.. code-block:: bash

    $ mkvirtualenv muckamuck
    $ pip install -r requirements.txt


Environment Variables
----------------------------------

Edit the virtualenv $ nano $VIRTUAL_ENV/bin/postactivate

.. code-block:: bash

      MUCKAMUCK_OUTPUT_DIRECTORY="output directory"
      MUCKAMUCK_DB_HOST="db host location"
      MUCKAMUCK_DB_NAME="database name"
      MUCKAMUCK_DB_USER_NAME="db user name"
      MUCKAMUCK_DB_USER_PASSWORD="db user password"
      MUCKAMUCK_SITES_DOMIAN="muckamuck.net"
