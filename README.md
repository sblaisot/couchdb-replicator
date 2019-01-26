# couchdb-replicator

A python program to replicate some or all databases between couchdb clusters.

## Installation

    $ python3 -m venv venv
    $ . ./venv/bin/activate
    $ pip install -r requirements.txt

## Usage

    usage: couchdb-replicator.py -s SOURCE -t TARGET [-h] [-a] [-i SKIP]
                                 [-c CONCURRENCY] [--use_target] [--system_dbs]
                                 [-p] [-v] [-q] [-d]
                                 [DB [DB ...]]

    Replicate databases between couchdb clusters

    required named arguments:
      -s SOURCE, --source SOURCE
                            The URL for the CouchDB cluster from which we will be replicating
      -t TARGET, --target TARGET
                            The URL for the CouchDB cluster from which we will be replicating

    positional arguments:
      DB                    Databases to replicate

    optional arguments:
      -h, --help            Show this help message and exit
      -a, --all             Replicate all dbs from source to destination.
                            Use with -i to replicate "all but ..."
      -i SKIP, --skip SKIP  Comma-separated list of db to skip (i.e.NOT synchronize)
      -c CONCURRENCY, --concurrency CONCURRENCY
                            Maximum number of simultaneous replications
      --use_target          Use the target's _replicate API when replicating.
                            By default, the source's _replicate API is used
      --system_dbs          Do not skip "system" databases starting with underscore
                            such as _users, _global_changes, etc...
      -p, --permanent       Add permanent continuous replication after first initial
                            replication
      -v, --verbose         Verbose
      -q, --quiet           Quiet. Do not show progress bar
      -d, --debug           Debug info such as details of the requests and responses.
                            Useful for determining why long replications are failing

## Examples

Replicate all databases on cluster1.example to cluster2.example except system dbs
(the ones that start with _ like _global_changes or _users):

    $ couchdb-replicator.py -s http://cluster1.example:5984 \
                            -t http://cluster2.example:5984 \
                            -a

Replicate all databases using SSL and authentication:

    $ couchdb-replicator.py -s https://admin1:secrect1@cluster1.example:6984 \
                            -t https://admin2:secrect2@cluster2.example:6984 \
                            -a

Replicate all databases except databases db1 and db2 and use 10 threads:

    $ couchdb-replicator.py -s http://cluster1.example:5984 \
                            -t http://cluster2.example:5984 \
                            -c 10 \
                            -i db1,db2 \
                            -a

Replicate only db1, db2 and db3 databases:

    $ couchdb-replicator.py -s https://admin1:secrect1@cluster1.example:6984 \
                            -t https://admin2:secrect2@cluster2.example:6984 \
                            db1 db2 db3

Make an initial replication of databases db1 and db2,
then setup continuous replication:

    $ couchdb-replicator.py -s https://admin1:secrect1@cluster1.example:6984 \
                            -t https://admin2:secrect2@cluster2.example:6984 \
                            -p \
                            db1 db2
