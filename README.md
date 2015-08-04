#muckamuck
A Multi-site Blog/Podcast Management System written in python.
As seen at [Mowich.net](http://mowich.net)


## Installation

*Tested only on Ubuntu Server 14.04.2 LTS*


**Instructions**


1. ```$ sudo apt-get update```
2. ```$ sudo apt-get upgrade```
3. ```$ sudo apt-get install build-essential libffi-dev python-dev```
3. Install Python pip: https://pip.pypa.io/en/latest/installing.html
4. Install Python virtualenv: https://virtualenv.pypa.io/en/latest/installation.html
5. Install Python virtualenvwrapper: https://virtualenvwrapper.readthedocs.org/en/latest/
6. Install Redis: http://redis.io/topics/quickstart If you have ```missing LSB tags and overrides``` see https://github.com/antirez/redis/issues/804 and use ```$ use sudo utils/install_server.sh```
7. Install MariaDB: https://downloads.mariadb.org/mariadb/repositories
8. Build nginx with ngx_pagespeed: https://developers.google.com/speed/pagespeed/module/build_ngx_pagespeed_from_source
9. ```$ mkdir muckamuck```
10. ```$ cd muckamuck```
11. ```$ mkvirtualenv muckamuck```
12. ```$ git clone https://github.com/jrigden/muckamuck.git```
13. ```$ cd muckamuck```
14. ```$ pip install -r requirements.txt```
15. ```$ cp dummy_config.py config.py```

##Basic Usage

```$ celery -A tasks worker -l info```

## Change Log

 1. Cleaned up github repo


## Todo

 - ~~Make todo list~~
 - Write install guide

##Testing

```$ py.test models.py```

```$ py.test render.py```

```$ py.test tasks.py```


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
