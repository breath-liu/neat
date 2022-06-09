import time
from logging import Logger

from celery import Task
from celery.utils.log import get_task_logger
from paramiko.channel import ChannelStderrFile, ChannelFile

import neat
from neat.src.service.celeryApp import app
from neat.src.service.sshclient import SshClient
from neat.src.service.sshclientTask import SshClientTask

logger = get_task_logger(__name__)


def __get_sshclient(host, port, user, password):
    client = SshClient(host, port, user, password)
    return client


@app.task(base=SshClientTask)
def command(server, cmd):
    client:SshClient = command.client(server)
    exit_code, stdout, stderr = client.command(cmd)
    return {'exit_code': exit_code, 'stdout': stdout, 'stderr': stderr}


@app.task(base=SshClientTask)
def scp_env(ip, local_path, remote_path):
    client = scp_env.client(ip)
    client.scp(local_path, remote_path)


@app.task(base=SshClientTask, bind=True)
def exe_script(self: Task, server, env_command, resources, run_command):
    self.update_state(state='PROGRESS', meta={'progress': f'connecting to {server.ip} ...'})
    client: SshClient = exe_script.client(server)
    self.update_state(state='PROGRESS', meta={'progress': f'scp {resources} to {neat.remote_workspace} ...'})
    client.scp(resources, f'{neat.remote_workspace}')
    self.update_state(state='PROGRESS', meta={'progress': f'run command {env_command} && cd {neat.remote_workspace} && {run_command}'})
    exit_code, stdout, stderr = client.command(f'{env_command} && cd {neat.remote_workspace} && {run_command}')
    return {'exit_code': exit_code, 'stdout': stdout, 'stderr': stderr}


@app.task(bind=True)
def hello(self, a, b):
    logger: Logger = get_task_logger(__name__)
    time.sleep(1)
    logger.info('abc')
    self.update_state(state="PROGRESS", meta={'progress': 50})
    time.sleep(1)
    logger.info('bcd')
    self.update_state(state="PROGRESS", meta={'progress': 90})
    time.sleep(1)
    return 1, 4, 8
