#!/usr/bin/env python3

import argparse
import datetime
import sys
import json
import time
import requests
import urllib.parse
import concurrent.futures
from argparse import RawTextHelpFormatter


DEFAULT_CONCURRENCY = 5


def printProgressBar(iteration,
                     total,
                     prefix='',
                     suffix='',
                     decimals=1,
                     length=100,
                     fill='█',
                     ):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent
                                  complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    if not sys.stdout.isatty():
        return
    percent = ('{0:.' + str(decimals) + 'f}').format(
                    100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\r{} |{}| {}% {}'.format(prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration >= total:
        print(' ' * (len(prefix) + length + len(suffix) + 11), end='\r')


def do_replicate(
                source,
                target,
                db,
                continuous=False,
                use_target=False,
                verbose=False,
                debug=False,
                ):
    """
    Replicate a database between couchdb clusters
    @params:
        source      - Required  : source cluster url
        target      - Required  : target cluster url
        db          - Required  : db to replicate
        continuous  - Optional  : add continuous replication (Boolean)
        use_target  - Optional  : use target's _replicate API (Boolean)
        verbose     - Optional  : print verbose messages (Boolean)
        debug       - Optional  : print debug informations (Boolean)
    """
    payload = {
            'source': '{}/{}'.format(source, db),
            'target': '{}/{}'.format(target, db),
            'create_target': True
            }
    replicate_url = '{}/_replicate'.format({False: source,
                                            True: target}.get(use_target))
    verbose_print(verbose, 'Starting replication of database {}'
                           .format(db))
    res = requests.post(replicate_url,
                        headers=dict({'Content-Type': 'application/json'}),
                        data=json.dumps(payload))
    if debug:
        print('Request POST {} with data {}'
              .format(res.url, json.dumps(payload)))
        print('HTTP response code {} with data {}'
              .format(res.status_code, res.text))
    if not res.json()['ok']:
        print('*** Failed to replicate database {}'.format(db))
        return

    verbose_print(verbose, 'Replication of database {} successful'
                           .format(db))

    if not continuous:
        return

    payload['continuous'] = True
    verbose_print(verbose,
                  'Setting up continuous replication of database {}'
                  .format(db))
    res = requests.post(
        replicate_url,
        headers=dict({'Content-Type': 'application/json'}),
        data=json.dumps(payload)
        )
    if debug:
        print('Request POST {} with data {}'
              .format(res.url, json.dumps(payload)))
        print('HTTP response code {} with data {}'
              .format(res.status_code, res.text))
    if not res.json()['ok']:
        print('*** Failed to setup continuous replication of database {}'
              .format(db))
        return
    verbose_print(verbose,
                  'Continuous replication of database {} successfully '
                  'setup'.format(db))


def parse_args(argv=sys.argv):
    """
    Parse arguments
    @params:
        argv        - Optional  : arguments
    """
    parser = argparse.ArgumentParser(
        description='Replicate databases between couchdb clusters',
        formatter_class=RawTextHelpFormatter,
        add_help=False)
    required_named = parser.add_argument_group('required named arguments')
    positional_named = parser.add_argument_group('positional arguments')
    optional_named = parser.add_argument_group('optional arguments')

    required_named.add_argument('-s',
                                '--source',
                                help='The URL for the CouchDB cluster from '
                                     'which we will be replicating',
                                action='store',
                                required=True)
    required_named.add_argument('-t',
                                '--target',
                                help='The URL for the CouchDB cluster from '
                                     'which we will be replicating',
                                action='store',
                                required=True)
    optional_named.add_argument('-h',
                                '--help',
                                action='help',
                                help='Show this help message and exit')
    optional_named.add_argument('-a',
                                '--all',
                                help='Replicate all dbs from source to '
                                     'destination.\n'
                                     'Use with -i to replicate "all but ..."',
                                action='store_true',
                                default=False)
    optional_named.add_argument('-i',
                                '--skip',
                                help='Comma-separated list of db to skip '
                                     '(i.e.NOT synchronize)',
                                action='store',
                                default=False)
    optional_named.add_argument('-c',
                                '--concurrency',
                                help='Maximum number of simultaneous '
                                     'replications',
                                action='store',
                                default=DEFAULT_CONCURRENCY)
    optional_named.add_argument('--use_target',
                                help='Use the target\'s _replicate API when '
                                     'replicating.\n'
                                     'By default, the source\'s _replicate '
                                     'API is used',
                                action='store_true',
                                default=False)
    optional_named.add_argument('--system_dbs',
                                help='Do not skip "system" databases starting '
                                     'with underscore\n'
                                     'such as _users, _global_changes, etc...',
                                action='store_true',
                                default=False)
    optional_named.add_argument('-p',
                                '--permanent',
                                help='Add permanent continuous replication '
                                     'after first initial\nreplication',
                                action='store_true',
                                default=False)
    optional_named.add_argument('-v',
                                '--verbose',
                                help='Verbose',
                                action='store_true',
                                default=False)
    optional_named.add_argument('-q',
                                '--quiet',
                                help='Quiet. Do not show progress bar',
                                action='store_true',
                                default=False)
    optional_named.add_argument('-d',
                                '--debug',
                                help='Debug info such as details of the '
                                     'requests and responses.\n'
                                     'Useful for determining why long '
                                     'replications are failing',
                                action='store_true',
                                default=False)
    positional_named.add_argument('DB',
                                  help='Databases to replicate',
                                  action='store',
                                  nargs='*')
    args = parser.parse_args()
    if not args.all and len(args.DB) == 0:
        parser.error('Need to specify database to replicate or --all')
    if args.all and len(args.DB) != 0:
        parser.error('--all and specifying dbs are mutually exclusive')
    return args


def verbose_print(verbose=False, *args):
    if verbose:
        print(*args)


def main(argv=sys.argv):
    args = parse_args(argv)

    if args.skip:
        skip_db = [x.strip() for x in args.skip.split(',')]
    else:
        skip_db = []

    if args.all:
        verbose_print(args.verbose, 'Getting list of all databases in source')
        res = requests.get('{}/_all_dbs'.format(args.source))
        if args.debug:
            print('Request GET {}'.format(res.url))
            print('HTTP response code {} with data {}'
                  .format(res.status_code, res.text))
        dbs = res.json()
    else:
        dbs = args.DB

    executor = concurrent.futures.ThreadPoolExecutor(
                                 max_workers=int(args.concurrency)
                                 )
    threads = []

    if not args.quiet:
        start_time = datetime.datetime.utcnow()
        print('Replication started at {}'.format(start_time))

    # Add all replications as asynchronous threads in thread pool
    for db in dbs:
        if db.startswith('_') and not args.system_dbs:
            verbose_print(args.verbose, 'Skipping system database {}'
                                        .format(db))
            continue

        if db in skip_db or urllib.parse.quote_plus(db) in skip_db:
            verbose_print(args.verbose, 'Skipping database {}'.format(db))
            continue

        threads.append(executor.submit(do_replicate,
                                       args.source,
                                       args.target,
                                       urllib.parse.quote_plus(db),
                                       continuous=args.permanent,
                                       use_target=args.use_target,
                                       verbose=args.verbose,
                                       debug=args.debug))

    # Wait for all threads to complete and show progress bar unless quiet
    total = len(threads)
    done_threads = []
    while len(done_threads) < total:
        new_threads_done = [thread for thread in threads
                            if thread not in done_threads and thread.done()]
        for thread in new_threads_done:
            # Die as soon as a thread raised an exception
            if thread.exception() is not None:
                raise(thread.exception())
        done_threads.extend(new_threads_done)
        if not args.quiet:
            printProgressBar(
                len(done_threads),
                total,
                prefix='Progress:',
                suffix='Complete',
                length=50
                )
        time.sleep(1)

    if not args.quiet:
        end_time = datetime.datetime.utcnow()
        print('Replication ended at {}'.format(end_time))
        elapsed = end_time - start_time
        print('Replication of {} databases took {}'
              .format(len(threads), elapsed))


if __name__ == '__main__':
    main()
