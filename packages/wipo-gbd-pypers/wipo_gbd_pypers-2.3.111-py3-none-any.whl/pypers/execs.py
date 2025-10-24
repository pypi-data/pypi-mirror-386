"""
 This file is part of Pypers.

 Pypers is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Pypers is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Pypers.  If not, see <http://www.gnu.org/licenses/>.
 """

import argparse
import sys
import os
import getpass
import glob
import re
import time
import traceback
import locale
import signal
from threading import Thread

from pypers.common import build_command_parser, apply_custom
from pypers.cli import STAGE
from pypers.cli.snapshot import Snapshot
from pypers.cli.stage_ori import StageOri
from pypers.cli.stage_gbd import StageGBD
from pypers.cli.stage_idx import StageIDX, StageIDXFromBucket
from pypers.cli.publish import Publish
from pypers.cli.ecs_manager import ECSManager
from pypers.cli.dynamo_manager import DynamoManager
from pypers.utils import utils as ut

from pypers.utils.execute import run_as
from pypers.core.pipelines import Pipeline
from pypers.core.step import Step
from pypers.core.supervisor import get_status_manager
from pypers.core.interfaces import msgbus, db


def _end_docker(_signal, _frame):
    get_status_manager().stop()
    signal.signal(signal.SIGINT, signal.SIG_DFL)

def bnd_docker():
    global supervisor

    configs = [
        {
            'name': ['--no-monitor'],
            'dest': 'no_supervisor',
            'help': 'Do not monitor',
            'action': 'store_true',
            'default': False
        }]
    args = build_command_parser(configs, '')
    supervised = not args.no_supervisor
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    locale.setlocale(locale.LC_CTYPE, 'en_US.UTF-8')
    user = getpass.getuser()
    # init the singleton
    get_status_manager(supervised=supervised).set_sanity()
    get_status_manager().set_status(busy=False)
    # trigger the sanity check endpoints
    signal.signal(signal.SIGINT, _end_docker)

    while get_status_manager().keep_alive():
        get_status_manager().set_sanity()
        body, id = msgbus.get_msg_bus().get_messges()
        if body and body.get('runid', None):
            msgbus.get_msg_bus().delete_message(id)
            get_status_manager().set_status(busy=True)
            #time.sleep(10)
            try:
                if body.get('index', None):
                    cfg = db.get_db().get_run_id_config(body.get('runid'),
                                                        body.get('collection'))
                    # create a step
                    step_index = Step.load_step(
                        body.get('runid'), body.get('collection'),
                        body.get('step'), sub_step=body.get('index'))

                    if not os.path.exists(step_index.output_dir):
                        os.makedirs(step_index.output_dir, 0o775)

                    # remove existing files, except step config
                    full_list = glob.glob(step_index.output_dir + "/*")
                    regex = re.compile("(input\.json|.*\.cfg)")
                    to_remove = filter(lambda f: not regex.search(f), full_list)
                    for entry in to_remove:
                        cmd = ['rm', '-rvf', entry]
                        (ec, err, out) = run_as(cmd=cmd, user=user)
                        if ec:
                            step_index.log.warning("failed to remove file %s: %s, %s" % (
                                entry, err, out))
                        else:
                            step_index.log.info("Removed %s" % entry)

                    # run step
                    step_index.run()
                    p = Pipeline(cfg.get('pipeline_configuration'))
                    p.load_completed()

                    step = Step.load_step(
                        body.get('runid'), body.get('collection'),
                        body.get('step'))
                    p.running[body.get('step')] = step
                    p.update_status()
                    p.parse_next()
                    msgbus.get_msg_bus().delete_message(id)

                elif body.get('step', None):
                    cfg = db.get_db().get_run_id_config(body.get('runid'),
                                                        body.get('collection'))
                    p = Pipeline(cfg.get('pipeline_configuration'))
                    p.load_completed()
                    p.run_step(body.get('step'))
                    msgbus.get_msg_bus().delete_message(id)
                else:
                    try:
                        config = Pipeline.load_cfg_from_db(body.get('collection'))
                        if 'sys_path' not in config:
                            config['sys_path'] = os.path.dirname(
                                os.path.realpath(body.get('collection')))
                    except Exception as e1:
                        raise e1

                    customs = ['pipeline.run_id=%s' % body.get('runid'),
                               'pipeline.type=%s' % body.get('type'),
                               'pipeline.forced_restarted=%s' % body.get('force_restart')]
                    if body.get('custom_config'):
                        customs.extend(body.get('custom_config'))
                    apply_custom(config, customs)

                    p = Pipeline(config, reset_logs=str(body.get('force_restart'))=='True')
                    if str(body.get('force_restart'))=='True':
                        msgbus.get_msg_bus().reset_history(p.run_id, p.collection)
                    p.load_completed(restart=str(body.get('force_restart'))=='True')
                    p.log.info("Running the pipeline...")
                    p.run()
            except Exception as e:
                if body.get('retry', False) is False:
                    msgbus.get_msg_bus().send_message(body.get('runid'),
                                                      type=body.get('type'),
                                                      step=body.get('step'),
                                                      index=body.get('index'),
                                                      collection=body.get('collection'),
                                                      restart=body.get('force_restart'),
                                                      restart_step=True,
                                                      custom_config=body.get('custom_config'),
                                                      retry=True)
                    prefix = 'Will retry: '
                    db.get_db_error().send_error(body.get('runid'), body.get('collection'), body,
                                                 "%s - %s- %s" % (prefix, id, traceback.format_exc()))
                else:
                    collection = body.get('collection')
                    if '_' in collection:
                        collection = collection.split('_')[0]
                    db.get_operation_db().completed(
                            body.get('runid'),
                            collection,
                            success=False)
                    prefix = "Will not retry: "
                    db.get_db_error().send_error(body.get('runid'), body.get('collection'), body,
                                                 "%s - %s- %s" % (prefix, id, traceback.format_exc()))
                    # Delete files from done table
                    db.get_done_file_manager().delete_done(body.get('collection'), body.get('runid'))
                    # Send error email.
                    errors = db.get_db_error().get_error(body.get('runid'), body.get('collection'))
                    if len(errors):
                        error_report = {
                            x['original_message']['step'] + x['original_message']['index']: x['error_trace'] for x in
                            errors}
                        subject = "Errors in images or document processing %s in %s" % (body.get('runid'), body.get('collection'))
                        html = ut.template_render(
                            'notify_errors.html',
                            collection=body.get('collection'),
                            reports=error_report,
                            runid=body.get('runid'))
                        default_recpients = os.environ.get(
                            "DEFAULT_RECIPIENTS", 'nicolas.hoibian@wipo.int,patrice.lopez@wipo.int').split(',')
                        ut.send_mail(
                            "gbd@wipo.int", default_recpients, subject, html=html,
                            server=os.environ.get("MAIL_SERVER", None),
                            password=os.environ.get("MAIL_PASS", None), username=os.environ.get("MAIL_USERNAME", None))
                break

        get_status_manager().set_status(busy=False)
        time.sleep(0.5)
    get_status_manager().stop()

def gbd_submit():

    doc = """
    Submit a pipeline to the cluster
    """
    configs = [
    {
        'name': ['pipeline_name'],
        'type': str,
        'help': 'the configuration name of the pipeline run in the database'
    },
    {
        'name': ['run_id'],
        'type': str,
        'help': 'the run id'
    },
    {
        'name': ['type'],
        'type': str,
        'help': 'the pipeline type'
     },
    {
        'name': ['collection'],
        'type': str,
        'help': 'the collection name'
     },
     {
        'name': ['--restart'],
        'dest': 'restart',
        'help': 'restart a pipeline from fetch',
        'action': 'store_true',
        'default': False
    },
    {
        'name': ['custom'],
        'type': str,
        'metavar': 'SECTION.PARAM=VALUE',
        'nargs': argparse.REMAINDER,
        'default': getpass.getuser(),
        'help': 'custom configuration to apply on top of configuration file.\n'
                'SECTION must be a subsection of the \'config\' section\n'
                '(several levels can be specified: SEC.SUBSEC.SUBSUBSEC, etc.'
                ')\nPARAM is any parameter in this section'
    }]

    args = build_command_parser(configs, doc)
    if args.pipeline_name == 'operations':
        collection = 'operations'
    elif args.pipeline_name == 'fetch':
        collection = args.collection
    else:
        collection = "%s_%s" % (args.collection, args.pipeline_name)
    override_output = False
    pipeline_type = args.type or ('brands' if collection.endswith('tm') else 'designs')

    for item in args.custom:
        if 'pipeline.output_dir' in item:
            override_output = True
            break

    if not override_output and os.environ.get('WORK_DIR', None):
        output_dir = os.path.join(os.environ['WORK_DIR'],
                                  args.run_id,
                                  pipeline_type,
                                  args.collection)

        os.makedirs(output_dir, exist_ok=True)
        args.custom.append('pipeline.output_dir=%s' % output_dir)

    msgbus.get_msg_bus().send_message(args.run_id,
                                      type=pipeline_type,
                                      collection=collection,
                                      restart=args.restart,
                                      custom_config=args.custom)


def gbd_stage_snapshot():

    doc = """
    Creates a snapshot form db in order to perform staging
    """
    configs = [
    {
        'name': ['type'],
        'type': str,
        'help': 'the pipeline type'
     },
    {
        'name': ['collection'],
        'type': str,
        'help': 'the collection name'
     },
    {
        'name': ['-o'],
        'type': str,
        'help': 'the path to snapshot',
        'default': './'
    }
    ]
    args = build_command_parser(configs, doc)
    snapshot = Snapshot(args.collection, args.type)
    snapshot.collect_data(path=args.o)


def gbd_stage_ori():

    doc = """
    Gets ori files for staging
    """
    configs = [
    {
        'name': ['snapshot'],
        'type': str,
        'help': 'the snapshot to run'
     },
    {
        'name': ['stage_type'],
        'type': str,
        'choices': [i for i in STAGE.get_choices()],
        'help': 'the stage type'
     }
    ]
    args = build_command_parser(configs, doc)
    executor = StageOri(args.snapshot, args.stage_type)
    executor.stage()


def gbd_stage_publish():

    doc = """
    Publishes the sync message to SQS when the end-to-end pypers pipelines are done.
    """
    configs = [
    {
        'name': ['run_id'],
        'type': str,
        'help': ' the run id to watch if pypers operation is done'
     }
    ]
    args = build_command_parser(configs, doc)
    executor = Publish(args.run_id)
    executor.publish()


def gbd_stage_gbd():

    doc = """
    Gets gbd files for staging
    """
    configs = [
    {
        'name': ['snapshot'],
        'type': str,
        'help': 'the snapshot to run'
     },
    {
        'name': ['stage_type'],
        'type': str,
        'choices': [i for i in STAGE.get_choices()],
        'help': 'the stage type'
     }
    ]
    args = build_command_parser(configs, doc)
    executor = StageGBD(args.snapshot, args.stage_type)
    executor.stage()

def gbd_stage_idx():

    doc = """
    Gets gbd files for staging
    """
    configs = [
    {
        'name': ['--snapshot'],
        'type': str,
        'help': 'the snapshot to run'

     },
    {
        'name': ['--type'],
        'type': str,
        'help': 'the pipeline type'

    },
    {
        'name': ['--collection'],
        'type': str,
        'help': 'the collection to get the files from bucket',

    },
    {
        'name': ['--run_id'],
        'type': str,
        'help': 'the run id'

    },
    ]
    args = build_command_parser(configs, doc)
    if not (args.snapshot or (args.collection and args.type and args.run_id)):
        raise Exception("Please complete the command: A snapshot file or a (type, collection, run id)")

    if args.snapshot:
        executor = StageIDX(args.snapshot, None)
        executor.stage()
    else:
        executor = StageIDXFromBucket(args.type, args.collection, args.run_id)
        executor.stage()


def gbd_ecs_manager():

    doc = """
    Manages the ecs cluster
    """
    configs = [
    {
        'name': ['action'],
        'type': str,
        'choices': ['start', 'stop', 'info'],
        'help': 'Action to perform'

     },
    {
        'name': ['--cluster'],
        'default': 'gbd-solr-ecs-cluster',
        'type': str,
        'help': 'The cluster name to perfom the action on'

     },
    {
        'name': ['--service'],
        'type': str,
        'choices': ['blue', 'green', 'solr', 'etl-etl'],
        'help': 'Service Name to perform the action on'

    },
    {
        'name': ['--nb_tasks'],
        'type': int,
        'default': 1,
        'help': 'The number of tasks to be started per service'

    }
    ]
    args = build_command_parser(configs, doc)
    if not args.action or (args.action != 'info' and not args.service):
        raise Exception("Please complete the command!")
    if args.action == 'info':
        ECSManager.info_cluster(args.cluster)
    if args.action == 'start':
        if args.service == 'solr':
            ECSManager.start_service(args.cluster, anti_pattern=['blue', 'green'], nb_tasks=args.nb_tasks)
        else:
            ECSManager.start_service(args.cluster, pattern=[args.service], nb_tasks=args.nb_tasks)
    if args.action == 'stop':
        if args.service == 'solr':
            ECSManager.stop_service(args.cluster, anti_pattern=['blue', 'green'])
        else:
            ECSManager.stop_service(args.cluster, pattern=[args.service])

def gbd_dynamo_manager():

    doc = """
    Manages the dynamo db
    """
    configs = [
    {
        'name': ['table'],
        'type': str,
        'help': 'Action to perform'

     },
    {
        'name': ['write_cap'],
        'type': int,
        'help': 'The write capacity desired'

     },
    {
        'name': ['read_cap'],
        'type': int,
        'help': 'The read capacity desired'

    },
    ]
    args = build_command_parser(configs, doc)
    DynamoManager.update_capacity(args.table, args.write_cap, args.read_cap)
