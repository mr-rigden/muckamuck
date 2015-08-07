#muckamuck

A Multi-site Blog/Podcast Management System written in python.
As seen at [Mowich.net](http://mowich.net)

## Status


[![GitHub version](https://badge.fury.io/gh/jrigden%2Fmuckamuck.svg)](http://badge.fury.io/gh/jrigden%2Fmuckamuck) [![Build Status](https://travis-ci.org/jrigden/muckamuck.svg?branch=master)](https://travis-ci.org/jrigden/muckamuck) [![Coverage Status](https://coveralls.io/repos/jrigden/muckamuck/badge.svg?branch=master&service=github)](https://coveralls.io/github/jrigden/muckamuck?branch=master) [![Dependency Status](https://gemnasium.com/jrigden/muckamuck.svg)](https://gemnasium.com/jrigden/muckamuck)

## Documentation
[![Documentation Status](https://readthedocs.org/projects/muckamuck/badge/?version=latest)](https://readthedocs.org/projects/muckamuck/?badge=latest)

## Contributors
**Jason Rigden**
## License
**The MIT License (MIT)**

Copyright (c) 2015 Jason Rigden

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.



## Ignore this part...

*Tested only on Ubuntu Server 14.04.2 LTS*
###Settings
1. Choose database name, database username, database password for MariaDB
2. Create output directory and note full path

###System
1. ```$ sudo apt-get update```
2. ```$ sudo apt-get upgrade```
3. ```$ sudo apt-get install build-essential libffi-dev python-dev git```
3. ```$ sudo apt-get install libmariadbclient-dev libssl-dev```
4. ```$ git clone https://github.com/jrigden/muckamuck.git```

###Python
1. ```$ cd muckamuck```
2. Install Python pip: https://pip.pypa.io/en/latest/installing.html
3. Install Python virtualenv: https://virtualenv.pypa.io/en/latest/installation.html
4. Install Python virtualenvwrapper: https://virtualenvwrapper.readthedocs.org/en/latest/
5. ```$ mkvirtualenv muckamuck```
5. ```$ pip install -r requirements.txt```

###Redis
1. Install Redis: http://redis.io/topics/quickstart If you have ```missing LSB tags and overrides``` see https://github.com/antirez/redis/issues/804 and use ```$ use sudo utils/install_server.sh```

###MariaDB
1. Install MariaDB: https://downloads.mariadb.org/mariadb/repositories
2. Login in to MariaDB as root ```$ mysql -u root -p```
3. ```CREATE DATABASE database_name;```
4. ```CREATE USER 'username'@'%' IDENTIFIED BY 'password';```
5. ```GRANT ALL PRIVILEGES ON database_name.* to 'username'@'%'      IDENTIFIED BY  'password';```
6. ```FLUSH PRIVILEGES;```

###Nginx with pagespeed
1. Build nginx with ngx_pagespeed: https://developers.google.com/speed/pagespeed/module/build_ngx_pagespeed_from_source
2. Need nginx config file

###Environment Variables
1. Edit the virtualenv ```$ nano $VIRTUAL_ENV/bin/postactivate```
2. Add ```export MUCKAMUCK_OUTPUT_DIRECTORY="output directory"```
3. Add ```export MUCKAMUCK_DB_HOST="db host location"```
4. Add ```export MUCKAMUCK_DB_NAME="database name"```
5. Add ```export MUCKAMUCK_DB_USER_NAME="db user name"```
6. Add ```export MUCKAMUCK_DB_USER_PASSWORD="db user password"```
7. Add ```export MUCKAMUCK_SITES_DOMIAN="muckamuck.net"```


###File System
1. ```$ python install.py```

##Testing
```$ py.test models.py```

```$ py.test render.py```

```$ py.test tasks.py```
