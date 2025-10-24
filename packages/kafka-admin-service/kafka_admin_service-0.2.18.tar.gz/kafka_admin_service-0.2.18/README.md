# kafka_admin_service

KAFKA管理类，提供用户创建、删除、列表查询、修改密码，提供主题创建、删除、列表查询，提供权限创建、删除、列表查询等基础管理功能。

## 安装

```
pip install kafka-admin-service
```

## KafkaAdminService类方法

- add_acl
- change_password
- create_topic
- create_topic_and_topic_user
- create_user
- delete_acl
- delete_all_topics
- delete_all_users
- delete_topic
- delete_topic_user_acls
- delete_user
- get_acls
- get_consumer_group_member_assignments
- get_consumer_group_members
- get_consumer_groups
- get_kafka_log_dirs
- get_kafka_version
- get_topics
- get_user_scrams
- get_users
- update_user
- validate_user_password



## 返回值说明

由于KafkaAdminService在底层以“外部命令调用”的方式调用了kafka/bin/目录下的管理命令，所以返回值中大多会出现returncode/stdout/stderr等字段。其中returncode表示kafka管理命令执行后的退出值，stdout表示kafka管理命令执行后的输出，stderr表示kafka管理命令执行后的错误输出。

## 对于KAFKA服务器配置的要求
1. 要求KAFKA集群使用了scram认证。
1. 要求KAFKA依赖的zookeeper不使用认证。
1. 要求应用运行时的当前目录是Kafka的根目录，或使用workspace指定kafka的根目录。
1. 要求已创建正确的./config/scram.jaas文件。
1. 要求已创建正确的./config/scram.client.properties文件。
1. 要求应用服务能正常访问kafka服务器以及zookeeper服务器，所以一般情况下可以将管理应用安装在kafka节点机上。

## ./config/scram.jaas模板

```
KafkaServer {
   org.apache.kafka.common.security.scram.ScramLoginModule required
   username="admin"
   password="xxxxxxxx";
};

KafkaClient {
   org.apache.kafka.common.security.scram.ScramLoginModule required
   username="admin"
   password="xxxxxxxx";
};
```

## ./config/scram.client.properties模板

```
security.protocol=SASL_PLAINTEXT
sasl.mechanism=SCRAM-SHA-256
```

## 常用的类初始化配置：kafka_admin_service_config.yml

加载配置文件，传递给KafkaAdminService创建方法。

```
zookeeper: localhost:2181
bootstrap_server: localhost:9092
workspace: /apprun/kafka/
command_config_file: "/apprun/config/scram.client.properties"
default_kafka_opts: "-Djava.security.auth.login.config=/apprun/config/scram.jaas"
topic_partitions: 16
topic_replication_factor: 3
apikeys:
    xxxxxxx:
        appid: xxxx
        other-appinfo: xxx
    yyyyyyy:
        appid: yyyy
        other-appinfo: yyy
```

## 启动kafka-admin-server服务器

```
kafka-admin-server --no-daemon -c config.yml start
```

## 版本历史

### v0.1.1

- First Release.

### v0.1.3

- 优化脚本依赖程序的路径检查和提示。
- 增加命令执行时间日志输出。

### v0.1.7

- 增加get_user_scrams方法，用于获取系统中用户的scram密码哈希信息。
- 增加validate_user_password方法，用于检验用户密码是否正确。
- 修正sdist在部分环境下安装时license文件缺失问题。
- 更新文档。

### v0.1.9

- 修正命令参数填充不完整的问题。
- 修正执行语句KAFKA_OPTS设置缺失的问题。

### v0.2.1

- 基于xmlrpc，引入kafka-admin-server。

### v0.2.14

- 增加get_consumer_group_member_assignments接口。
- 增加get_consumer_group_members接口。
- 增加get_consumer_groups接口。
- 增加get_kafka_version接口。
- 增加get_kafka_log_dirs接口。
- 删除无效的接口导出。

### v0.2.17

- 增加get_user_configs接口。

### v0.2.18

- Doc update.
