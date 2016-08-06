.. toctree::
   :maxdepth: 2

Doing requests
==============

Content-type when sending a body, output content-type, etc.

Return codes
------------

This is a table that represents the expected return codes for general requests:

+------------------------+------------+-------------------+------------------+
| HTTP Verb              | CRUD       | Entire collection | Specific item    |
|                        |            | (eg. /comics)     | (eg. /comics/id) |
+========================+============+===================+==================+
| POST                   | Create     | 201               | 201              |
+------------------------+------------+-------------------+------------------+
| GET                    | Read       | 200               | 200              |
+------------------------+------------+-------------------+------------------+
| PUT                    | Update     | 204               | 204              |
+------------------------+------------+-------------------+------------------+
| DELETE                 | Delete     | 204               | 204              |
+------------------------+------------+-------------------+------------------+
