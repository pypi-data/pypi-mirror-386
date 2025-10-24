import os
import re
import time
import json
import typing
import subprocess
import logging
import platform
import base64

from scramp import ScramMechanism
from fastutils import listutils


logger = logging.getLogger(__name__)


class KafkaAdminService(object):
    """
    1. You must setup your kafka instance with scram authenticate.
    2. You are using zookeeper without authenticate.
    3. You must make sure you are working at kafka's root folder.
    4. You must have an GOOD ./config/scram.jaas.
    5. You must have an GOOD ./config/scram.client.properties.
    6. You can access both zookeeper and kafka on your application server.
    """

    class Operations:
        Describe = "DESCRIBE"
        DescribeConfigs = "DESCRIBE_CONFIGS"
        Alter = "ALTER"
        Read = "READ"
        Delete = "DELETE"
        Create = "CREATE"
        All = "ALL"
        Write = "WRITE"
        AlterConfigs = "ALTER_CONFIGS"

    default_kafka_configs_cmd = "./bin/kafka-configs.sh"
    default_kafka_topics_cmd = "./bin/kafka-topics.sh"
    default_kafka_acls_cmd = "./bin/kafka-acls.sh"
    default_kafka_consumer_groups_cmd = "./bin/kafka-consumer-groups.sh"
    default_kafka_log_dirs_cmd = "./bin/kafka-log-dirs.sh"

    default_command_config_file = "./config/scram.client.properties"
    default_kafka_opts = "-Djava.security.auth.login.config=./config/scram.jaas"

    default_topic_partitions = 16
    default_topic_replication_factor = 3
    default_cmd_execute_timeout = 30
    default_admin_username = "admin"

    default_create_user_cmd_template = """{kafka_configs_cmd} --zookeeper {zookeeper} --alter --add-config 'SCRAM-SHA-256=[password={password}],SCRAM-SHA-512=[password={password}]' --entity-type users --entity-name {username}"""
    default_get_users_cmd_template = """{kafka_configs_cmd} --zookeeper {zookeeper} --describe  --entity-type users"""
    default_delete_user_cmd_template = """{kafka_configs_cmd} --zookeeper {zookeeper} --alter --delete-config SCRAM-SHA-256,SCRAM-SHA-512 --entity-type users --entity-name {username}"""
    default_get_kafka_version_cmd_template = """{kafka_configs_cmd} --bootstrap-server {bootstrap_server} --command-config {command_config_file} --version"""

    default_create_topic_cmd_template = """{kafka_topics_cmd} --bootstrap-server {bootstrap_server} --command-config {command_config_file} --create --topic {topic_name} --partitions {topic_partitions} --replication-factor {topic_replication_factor}"""
    default_get_topics_cmd_template = """{kafka_topics_cmd} --bootstrap-server {bootstrap_server} --command-config {command_config_file}  --list"""
    default_delete_topic_cmd_template = """{kafka_topics_cmd} --bootstrap-server {bootstrap_server} --command-config {command_config_file} --delete --topic {topic_name} --force"""

    default_add_acl_cmd_template = """{kafka_acls_cmd} --bootstrap-server {bootstrap_server} --command-config {command_config_file} --add --topic {topic_name} --allow-principal User:{username} --operation {operation} --force"""
    default_get_acls_cmd_template = """{kafka_acls_cmd} --bootstrap-server {bootstrap_server} --command-config {command_config_file} --list"""
    default_delete_acl_cmd_template = """{kafka_acls_cmd} --bootstrap-server {bootstrap_server} --command-config {command_config_file} --remove --topic {topic_name} --allow-principal User:{username} --operation {operation} --force"""

    default_get_consumer_groups_cmd_template = """{kafka_consumer_groups_cmd} --bootstrap-server {bootstrap_server} --command-config {command_config_file} --list --timeout={timeout}"""
    default_get_consumer_group_members_cmd_template = """{kafka_consumer_groups_cmd} --bootstrap-server {bootstrap_server} --command-config {command_config_file} --group {consumer_group_name} --describe --members --verbose --timeout={timeout}"""
    default_get_consumer_group_member_assignments_cmd_template = """{kafka_consumer_groups_cmd} --bootstrap-server {bootstrap_server} --command-config {command_config_file} --group {consumer_group_name} --describe --verbose --timeout {timeout}"""

    default_get_kafka_log_dirs_cmd_template = """{kafka_log_dirs_cmd} --bootstrap-server {bootstrap_server} --command-config {command_config_file} --describe"""

    def get_default_zookeeper(self):
        return "{hostname}:2181".format(hostname=platform.node())

    def get_default_bootstrap_server(self):
        return "{hostname}:9092".format(hostname=platform.node())

    def get_default_workspace(self):
        return os.getcwd()

    def is_file_exists(self, filename):
        filename = os.path.join(self.workspace, filename)
        return os.path.exists(filename)

    def __init__(self, config=None):
        self.config = config or {}

        self.kafka_configs_cmd = self.config.get("kafka_configs_cmd", self.default_kafka_configs_cmd)
        self.kafka_topics_cmd = self.config.get("kafka_topics_cmd", self.default_kafka_topics_cmd)
        self.kafka_acls_cmd = self.config.get("kafka_acls_cmd", self.default_kafka_acls_cmd)
        self.kafka_consumer_groups_cmd = self.config.get("kafka_consumer_groups_cmd", self.default_kafka_consumer_groups_cmd)
        self.kafka_log_dirs_cmd = self.config.get("kafka_log_dirs_cmd", self.default_kafka_log_dirs_cmd)

        self.zookeeper = self.config.get("zookeeper", self.get_default_zookeeper())
        self.bootstrap_server = self.config.get("bootstrap_server", self.get_default_bootstrap_server())
        self.kafka_opts = self.config.get("kafka_opts", self.default_kafka_opts)
        self.command_config_file = self.config.get("command_config_file", self.default_command_config_file)

        self.create_user_cmd_template = self.config.get("create_user_cmd_template", self.default_create_user_cmd_template)
        self.get_users_cmd_template = self.config.get("get_users_cmd_template", self.default_get_users_cmd_template)
        self.delete_user_cmd_template = self.config.get("delete_user_cmd_template", self.default_delete_user_cmd_template)
        self.get_kafka_version_cmd_template = self.config.get("get_kafka_version_cmd_template", self.default_get_kafka_version_cmd_template)

        self.create_topic_cmd_template = self.config.get("create_topic_cmd_template", self.default_create_topic_cmd_template)
        self.get_topics_cmd_template = self.config.get("get_topics_cmd_template", self.default_get_topics_cmd_template)
        self.delete_topic_cmd_template = self.config.get("delete_topic_cmd_template", self.default_delete_topic_cmd_template)
        
        self.add_acl_cmd_template = self.config.get("add_acl_cmd_template", self.default_add_acl_cmd_template)
        self.get_acls_cmd_template = self.config.get("get_acls_cmd_template", self.default_get_acls_cmd_template)
        self.delete_acl_cmd_template = self.config.get("delete_acl_cmd_template", self.default_delete_acl_cmd_template)
        
        self.get_consumer_groups_cmd_template = self.config.get("get_consumer_groups_cmd_template", self.default_get_consumer_groups_cmd_template)
        self.get_consumer_group_members_cmd_template = self.config.get("get_consumer_group_members_cmd_template", self.default_get_consumer_group_members_cmd_template)
        self.get_consumer_group_member_assignments_cmd_template = self.config.get("get_consumer_group_member_assignments_cmd_template", self.default_get_consumer_group_member_assignments_cmd_template)

        self.get_kafka_log_dirs_cmd_template = self.config.get("get_kafka_log_dirs_cmd_template", self.default_get_kafka_log_dirs_cmd_template)

        self.topic_partitions = self.config.get("topic_partitions", self.default_topic_partitions)
        self.topic_replication_factor = self.config.get("topic_replication_factor", self.default_topic_replication_factor)
        self.cmd_execute_timeout = self.config.get("cmd_execute_timeout", self.default_cmd_execute_timeout)
        self.admin_username = self.config.get("admin_username", self.default_admin_username)

        self.workspace = self.config.get("workspace", self.get_default_workspace())

        self.command_template_parameters = {
            "kafka_configs_cmd": self.kafka_configs_cmd,
            "kafka_topics_cmd": self.kafka_topics_cmd,
            "kafka_acls_cmd": self.kafka_acls_cmd,
            "kafka_consumer_groups_cmd": self.kafka_consumer_groups_cmd,
            "kafka_log_dirs_cmd": self.kafka_log_dirs_cmd,
            
            "zookeeper": self.zookeeper,
            "bootstrap_server": self.bootstrap_server,
            "kafka_opts": self.kafka_opts,
            "command_config_file": self.command_config_file,

            "topic_partitions": self.topic_partitions,
            "topic_replication_factor": self.topic_replication_factor,
            "timeout": self.cmd_execute_timeout * 1000,
        }

        path = os.path.abspath(os.path.join(self.workspace, self.kafka_configs_cmd))
        if not self.is_file_exists(path):
            logger.error(f"kafka_configs_cmd {path} not exists...")
        
        path = os.path.abspath(os.path.join(self.workspace, self.kafka_topics_cmd))
        if not self.is_file_exists(path):
            logger.error(f"kafka_topics_cmd {path} not exists...")

        path = os.path.abspath(os.path.join(self.workspace, self.kafka_acls_cmd))
        if not self.is_file_exists(path):
            logger.error(f"kafka_acls_cmd {path} not exists...")

        path = os.path.abspath(os.path.join(self.workspace, self.command_config_file))
        if not self.is_file_exists(self.command_config_file):
            logger.error(f"command_config_file {path} not exists...")

        scram_jaas = re.findall("-Djava.security.auth.login.config=([^\ ]*)", self.kafka_opts)[0]
        path = os.path.abspath(os.path.join(self.workspace, scram_jaas))
        if not self.is_file_exists(path):
            logger.error(f"scram_jaas {path} not exists...")

    
    def execute(self, cmd, kafka_opts=None, timeout=None)  -> typing.Tuple[int, str, str]:
        """Returns [returncode, stdout, stderr]"""
        timeout = timeout or self.cmd_execute_timeout
        stime = time.time()
        if kafka_opts:
            extra_env = os.environ
            extra_env["KAFKA_OPTS"] = kafka_opts
            proc = subprocess.Popen(cmd, shell=True, universal_newlines=True, cwd=self.workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=extra_env)
        else:
            proc = subprocess.Popen(cmd, shell=True, universal_newlines=True, cwd=self.workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate(timeout=timeout)
        etime = time.time()
        dtime = etime - stime
        logger.info(f"Execute command [[[{cmd}]]] cost {dtime} seconds.")
        return proc.returncode, stdout, stderr

    def update_user(self, username, password) -> typing.Tuple[int, str, str]:
        """Returns [returncode, stdout, stderr]"""
        params = {}
        params.update(self.command_template_parameters)
        params.update({
            "username": username,
            "password": password,
        })
        cmd = self.create_user_cmd_template.format(**params)
        return self.execute(cmd, kafka_opts=self.kafka_opts)

    def create_user(self, username, password) -> typing.Tuple[int, str, str]:
        """Returns [returncode, stdout, stderr]"""
        return self.update_user(username, password)

    def change_password(self, username, password) -> typing.Tuple[int, str, str]:
        """Returns [returncode, stdout, stderr]"""
        return self.update_user(username, password)

    def get_users(self) -> typing.Tuple[int, list, str, str]:
        """Returns [returncode, users, stdout, stderr]
        """
        params = {}
        params.update(self.command_template_parameters)
        cmd = self.get_users_cmd_template.format(**params)
        returncode, stdout, stderr = self.execute(cmd, kafka_opts=self.kafka_opts)
        if returncode == 0:
            users = re.findall("""Configs for user-principal '(.*)' are""", stdout)
            return returncode, users, stdout, stderr
        else:
            return returncode, [], stdout, stderr

    def get_user_configs(self) -> typing.Tuple[int, typing.Dict[str, dict], str, str]:
        """Returns [returncode, user_configs, stdout, stderr]"""
        params = {}
        params.update(self.command_template_parameters)
        cmd = self.get_users_cmd_template.format(**params)
        returncode, stdout, stderr = self.execute(cmd, kafka_opts=self.kafka_opts)
        if returncode == 0:
            user_configs = {}
            for line in stdout.splitlines():
                if line.startswith("Configs for user-principal '"):
                    username = re.findall("""Configs for user-principal '(.*)' are""", line)[0]
                    scrams = re.findall('(SCRAM-SHA-\d*)=salt=([^,]*),stored_key=([^,]*),server_key=([^,]*),iterations=(\d+)', line)
                    user_scrams = []
                    for scram in scrams:
                        user_scrams.append({
                            "mechanism": scram[0],
                            "salt": scram[1],
                            "stored_key": scram[2],
                            "server_key": scram[3],
                            "iterations": int(scram[4]),
                        })
                    user_configs[username] = {
                        "scrams": user_scrams,
                    }
            return returncode, user_configs, stdout, stderr
        else:
            return returncode, [], stdout, stderr

    def get_user_scrams(self, username) -> typing.Tuple[int, typing.List[dict], str, str]:
        """Returns [returncode, user scrams, stdout, stderr]"""
        params = {}
        params.update(self.command_template_parameters)
        cmd = self.get_users_cmd_template.format(**params)
        returncode, stdout, stderr = self.execute(cmd, kafka_opts=self.kafka_opts)
        if returncode == 0:
            startswith = f"Configs for user-principal '{username}' are"
            for line in stdout.splitlines():
                if line.startswith(startswith):
                    scrams = re.findall('(SCRAM-SHA-\d*)=salt=([^,]*),stored_key=([^,]*),server_key=([^,]*),iterations=(\d+)', line)
                    user_scrams = []
                    for scram in scrams:
                        user_scrams.append({
                            "mechanism": scram[0],
                            "salt": scram[1],
                            "stored_key": scram[2],
                            "server_key": scram[3],
                            "iterations": int(scram[4]),
                        })
                    return 0, user_scrams, "", ""
            return 1, {}, stdout, f"Config for user-principal '{username}' not found."
        else:
            return returncode, {}, stdout, stderr

    def validate_user_password(self, username, password) -> typing.Tuple[int, bool, str, str]:
        """Returns [returncode, validate_result, stdout, stderr]"""
        returncode, user_scrams, stdout, stderr = self.get_user_scrams(username)
        if returncode != 0:
            return returncode, None, stdout, stderr
        for user_scram in user_scrams:
            mechanism = user_scram["mechanism"]
            salt = user_scram["salt"]
            stored_key = user_scram["stored_key"]
            server_key = user_scram["server_key"]
            iteration_count = user_scram["iterations"]
            sm = ScramMechanism(mechanism=mechanism)
            new_salt, new_stored_key, new_server_key, new_iteration_count = sm.make_auth_info(
                password,
                iteration_count=iteration_count,
                salt=base64.decodebytes(salt.encode()),
                )
            new_salt = base64.encodebytes(new_salt).decode().replace("\n", "")
            new_stored_key = base64.encodebytes(new_stored_key).decode().replace("\n", "")
            new_server_key = base64.encodebytes(new_server_key).decode().replace("\n", "")
            if new_stored_key != stored_key:
                return 1, False, f"user_scram={user_scram}, new_salt={new_salt}, new_stored_key={new_stored_key}, new_server_key={new_server_key}, new_iteration_count={new_iteration_count}", f"{mechanism} validate failed, stored_key NOT matched."
            if new_server_key != server_key:
                return 1, False, f"user_scram={user_scram}, new_salt={new_salt}, new_stored_key={new_stored_key}, new_server_key={new_server_key}, new_iteration_count={new_iteration_count}", f"{mechanism} validate failed, server_key NOT matched."
        return 0, True, "", ""

    def delete_user(self, username) -> typing.Tuple[int, str, str]:
        """Returns [returncode, stdout, stderr]"""
        params = {}
        params.update(self.command_template_parameters)
        params.update({
            "username": username,
        })
        cmd = self.delete_user_cmd_template.format(**params)
        return self.execute(cmd, kafka_opts=self.kafka_opts)

    def create_topic(self, topic_name, topic_partitions=None, topic_replication_factor=None) -> typing.Tuple[int, str, str]:
        """Returns [returncode, stdout, stderr]"""
        topic_partitions = topic_partitions or self.topic_partitions
        topic_replication_factor = topic_replication_factor or self.topic_replication_factor

        params = {}
        params.update(self.command_template_parameters)
        params.update({
            "topic_name": topic_name,
            "topic_partitions": topic_partitions,
            "topic_replication_factor": topic_replication_factor,
        })
        cmd = self.create_topic_cmd_template.format(**params)
        return self.execute(cmd, kafka_opts=self.kafka_opts)

    def get_topics(self) -> typing.Tuple[int, list, str, str]:
        """Returns [returncode, topics, stdout, stderr]"""
        params = {}
        params.update(self.command_template_parameters)
        cmd = self.get_topics_cmd_template.format(**params)
        returncode, stdout, stderr = self.execute(cmd, kafka_opts=self.kafka_opts)
        if returncode == 0:
            topics = stdout.splitlines()
            return returncode, topics, stdout, stderr
        else:
            return returncode, [], stdout, stderr

    def delete_topic(self, topic_name) -> typing.Tuple[int, str, str]:
        """Returns [returncode, stdout, stderr]"""
        params = {}
        params.update(self.command_template_parameters)
        params.update({
            "topic_name": topic_name,
        })
        cmd = self.delete_topic_cmd_template.format(**params)
        return self.execute(cmd, kafka_opts=self.kafka_opts)

    def add_acl(self, topic_name, username, operation) -> typing.Tuple[int, str, str]:
        """Returns [returncode, stdout, stderr]"""
        params = {}
        params.update(self.command_template_parameters)
        params.update({
            "topic_name": topic_name,
            "username": username,
            "operation": operation,
        })
        cmd = self.add_acl_cmd_template.format(**params)
        return self.execute(cmd, kafka_opts=self.kafka_opts)

    def delete_acl(self, topic_name, username, operation) -> typing.Tuple[int, str, str]:
        """Returns [returncode, stdout, stderr]"""
        params = {}
        params.update(self.command_template_parameters)
        params.update({
            "topic_name": topic_name,
            "username": username,
            "operation": operation,
        })
        cmd = self.delete_acl_cmd_template.format(**params)
        return self.execute(cmd, kafka_opts=self.kafka_opts)

    def get_acls(self) -> typing.Tuple[int, list, str, str]:
        """Returns [returncode, users, stdout, stderr]"""
        params = {}
        params.update(self.command_template_parameters)
        cmd = self.get_acls_cmd_template.format(**params)
        returncode, stdout, stderr = self.execute(cmd, kafka_opts=self.kafka_opts)

        acls = {}
        if returncode == 0:
            current_topic_name = None
            current_topic_acls = {}
            for line in stdout.splitlines():
                if line.startswith("Current ACLs for resource `ResourcePattern(resourceType=TOPIC, name="):
                    current_topic_name = re.findall("name=(.*), patternType=", line)[0]
                    if current_topic_name and (not current_topic_name in acls):
                        acls[current_topic_name] = {}
                    current_topic_acls = acls[current_topic_name]
                else:
                    acl_pairs = re.findall("principal=User:(.*), host=\*, operation=(.*), permissionType=ALLOW", line)
                    
                    for username, operation in acl_pairs:
                        if not username in current_topic_acls:
                            current_topic_acls[username] = []
                        current_topic_acls[username].append(operation)

        return returncode, acls, stdout, stderr

    def delete_all_topics(self):
        deleted_topics = []
        errors = {}
        returncode, topics, stdout, stderr = self.get_topics()
        if returncode == 0:
            for topic_name in topics:
                returncode, stdout, stderr = self.delete_topic(topic_name)
                if returncode == 0:
                    deleted_topics.append(topic_name)
                else:
                    errors["topic_name"] = {
                        "stdout": stdout,
                        "stderr": stderr,
                    }
        else:
            errors["_get_topics"] = {
                "stdout": stdout,
                "stderr": stderr,
            }
        return {
            "deleted_topics": deleted_topics,
            "errors": errors,
        }

    def delete_all_users(self, preserves=None):
        preserves = preserves or []
        if isinstance(preserves, str):
            preserves = [preserves]
        if not self.admin_username in preserves:
            preserves.append(self.admin_username)
        deleted_users = []
        errors = {}
        returncode, users, stdout, stderr = self.get_users()
        if returncode == 0:
            for user in users:
                if user in preserves:
                    continue
                returncode, stdout, stderr = self.delete_user(user)
                if returncode == 0:
                    deleted_users.append(user)
                else:
                    errors[user] = {
                        "stdout": stdout,
                        "stderr": stderr,
                    }
        else:
            errors["_get_users"] = {
                "stdout": stdout,
                "stderr": stderr,
            }
        return {
            "deleted_users": deleted_users,
            "preserves": preserves,
            "errors": errors,
        }

    def create_topic_and_topic_user(self, topic_name, username, password, topic_partitions=None, topic_replication_factor=None):
        """Create a topic, create an user, and give read,write,describe acls to the user on the topic."""
        create_topic_returncode, create_topic_stdout, create_topic_stderr = self.create_topic(topic_name, topic_partitions, topic_replication_factor)
        create_user_returncode, create_user_stdout, create_user_stderr = self.create_user(username, password)
        add_read_acl_returncode, add_read_acl_stdout, add_read_acl_stderr = self.add_acl(topic_name, username, self.Operations.Read)
        add_write_acl_returncode, add_write_acl_stdout, add_write_acl_stderr = self.add_acl(topic_name, username, self.Operations.Write)
        add_describe_acl_returncode, add_describe_acl_stdout, add_describe_acl_stderr = self.add_acl(topic_name, username, self.Operations.Describe)

        return {
            "returncode": create_topic_returncode + create_user_returncode + add_read_acl_returncode + add_write_acl_returncode + add_describe_acl_returncode,
            "returncodes": {
                "create_topic": create_topic_returncode,
                "create_user": create_user_returncode,
                "add_read_acl": add_read_acl_returncode,
                "add_write_acl": add_write_acl_returncode,
                "add_describe_acl": add_describe_acl_returncode,
            },
            "stdout": {
                "create_topic": create_topic_stdout,
                "create_user": create_user_stdout,
                "add_read_acl": add_read_acl_stdout,
                "add_write_acl": add_write_acl_stdout,
                "add_describe_acl": add_describe_acl_stdout,
            },
            "stderr": {
                "create_topic": create_topic_stderr,
                "create_user": create_user_stderr,
                "add_read_acl": add_read_acl_stderr,
                "add_write_acl": add_write_acl_stderr,
                "add_describe_acl": add_describe_acl_stderr,
            }
        }

    def delete_topic_user_acls(self, topic_name, username):
        """Delete all the user's acls on the given topic"""
        deleted_acls = []
        errors = {}
        returncode, acls, stdout, stderr = self.get_acls()
        if returncode == 0:
            ops = acls.get(topic_name, {}).get(username, [])
            for op in ops:
                returncode, stdout, stderr = self.delete_acl(topic_name, username, op)
                if returncode == 0:
                    deleted_acls.append((topic_name, username, op))
                else:
                    errors[op] = {
                        "stdout": stdout,
                        "stderr": stderr,
                    }
        else:
            errors["_get_acls"] = {
                "stdout": stdout,
                "stderr": stderr,
            }
        return {
            "topic_name": topic_name,
            "username": username,
            "deleted_acls": deleted_acls,
            "errors": errors,
        }

    def get_consumer_groups(self) -> typing.Tuple[int, typing.List[str], str, str]:
        """Returns [returncode, consumer_group_names, stdout, stderr]
        """
        params = {}
        params.update(self.command_template_parameters)
        cmd = self.get_consumer_groups_cmd_template.format(**params)
        returncode, stdout, stderr = self.execute(cmd, kafka_opts=self.kafka_opts)
        if returncode == 0:
            consumer_group_names = stdout.splitlines()
            return returncode, consumer_group_names, stdout, stderr
        else:
            return returncode, [], stdout, stderr

    def get_consumer_group_members(self, consumer_group_name) -> typing.Tuple[int, list, str, str]:
        """Returns [returncode, consumer_group_members, stdout, stderr]

        A consumer group member is a dict, e.g.
        {
            "group": "testgroup",
            "consumer_id": "testgroupconsumer-1-xxxx",
            "client_id": "testgroupconsumer-1",
            "host": "localhost/127.0.0.1",
            "partitions": 3, # assigned partitions number
            "assignments": [
                "EXAMPLE_TOPIC_NAME(10,11,12)",
            ]
        }
        """
        params = {}
        params.update(self.command_template_parameters)
        params.update({
            "consumer_group_name": consumer_group_name,
        })
        cmd = self.get_consumer_group_members_cmd_template.format(**params)
        returncode, stdout, stderr = self.execute(cmd, kafka_opts=self.kafka_opts)
        if returncode == 0:
            consumer_group_members = []
            for line in stdout.splitlines():
                if line.startswith(consumer_group_name):
                    lineinfo = line.split(maxsplit=5)
                    info = listutils.list2dict(lineinfo, [
                        "group",
                        "consumer_id",
                        "host",
                        "client_id",
                        "partitions",
                        ("assignments", "")
                    ])
                    info["assignments"] = info["assignments"].split(", ")
                    consumer_group_members.append(info)
            return returncode, consumer_group_members, stdout, stderr
        else:
            return returncode, [], stdout, stderr

    def get_consumer_group_member_assignments(self, consumer_group_name, timeout=60) -> typing.Tuple[int, list, str, str]:
        """Returns [returncode, consumer_group_member_assignments, stdout, stderr]

        A consumer group member assignment is a dict, e.g.
        {
            "group": "testgroup",
            "topic": "EXAMPLE_TOPIC_NAME",
            "partition": 13,
            "current_offset": 1,
            "log_end_offset": 3,
            "lag" 0,
            "consumer_id": "testgroupconsumer-1-xxxx",
            "host": "localhost/127.0.0.1",
            "client_id": "testgroupconsumer-1",
        }
        """
        params = {}
        params.update(self.command_template_parameters)
        params.update({
            "consumer_group_name": consumer_group_name,
            "timeout": timeout*1000,
        })
        cmd = self.get_consumer_group_member_assignments_cmd_template.format(**params)
        returncode, stdout, stderr = self.execute(cmd, kafka_opts=self.kafka_opts, timeout=timeout)
        if returncode == 0:
            consumer_group_member_assignments = []
            for line in stdout.splitlines():
                if line.startswith(consumer_group_name):
                    lineinfo = line.split()
                    info = listutils.list2dict(lineinfo, [
                        "group",
                        "topic",
                        "partition",
                        "current_offset",
                        "log_end_offset",
                        "lag",
                        "consumer_id",
                        "host",
                        "client_id",
                    ])
                    consumer_group_member_assignments.append(info)
            return returncode, consumer_group_member_assignments, stdout, stderr
        else:
            return returncode, [], stdout, stderr

    def get_kafka_version(self) -> typing.Tuple[int, str, str, str]:
        """Returns [returncode, version_string, stdout, stderr]
        """
        params = {}
        params.update(self.command_template_parameters)
        cmd = self.get_kafka_version_cmd_template.format(**params)
        returncode, stdout, stderr = self.execute(cmd, kafka_opts=self.kafka_opts)
        if returncode == 0:
            version = stdout.strip()
            return returncode, version, stdout, stderr
        else:
            return returncode, [], stdout, stderr

    def get_kafka_log_dirs(self) -> typing.Tuple[int, dict, str, str]:
        """Returns [returncode, log_dirs_info, stdout, stderr]
        """
        params = {}
        params.update(self.command_template_parameters)
        cmd = self.get_kafka_log_dirs_cmd_template.format(**params)
        returncode, stdout, stderr = self.execute(cmd, kafka_opts=self.kafka_opts)
        if returncode == 0:
            log_dirs_info = {}
            for line in stdout.splitlines():
                try:
                    log_dirs_info = json.loads(line)
                except:
                    pass
            return returncode, log_dirs_info, stdout, stderr
        else:
            return returncode, [], stdout, stderr
