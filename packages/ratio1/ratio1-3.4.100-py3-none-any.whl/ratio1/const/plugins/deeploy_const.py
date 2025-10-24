"""
Examples:

- plugin_signature: "A_SIMPLE_PLUGIN"
- pipeline_input_type: "ExampleDatastream"

"""
from time import time
from uuid import uuid4

class DEEPLOY_KEYS:
  STATUS = "status"
  ERROR = "error"
  TRACE = "trace"
  REQUEST = "request"
  RESULT = "result"
  RETURN_REQUEST = "return_request"
  STATUS_DETAILS = "status_details"
  APPS = "apps"
  APP_ID = "app_id"
  NONCE = "nonce"
  APP_ALIAS = "app_alias"
  PLUGIN_SIGNATURE = "plugin_signature"
  TARGET_NODES = "target_nodes"
  TARGETS = "targets"
  TARGET_NODES_COUNT = "target_nodes_count"
  AUTH = "auth"
  CHAINSTORE_RESPONSE = "chainstore_response"
  PIPELINE_INPUT_TYPE = "pipeline_input_type"
  PIPELINE_INPUT_URI = "pipeline_input_uri"
  # App params keys
  APP_PARAMS = "app_params"
  APP_PARAMS_IMAGE = "IMAGE"
  APP_PARAMS_CR = "CR"
  APP_PARAMS_CR_USER = "CR_USER"
  APP_PARAMS_CR_PASSWORD = "CR_PASSWORD"
  APP_PARAMS_RESTART_POLICY = "RESTART_POLICY"
  APP_PARAMS_IMAGE_PULL_POLICY = "IMAGE_PULL_POLICY"
  APP_PARAMS_NGROK_EDGE_LABEL = "NGROK_EDGE_LABEL"
  APP_PARAMS_ENV = "ENV"
  APP_PARAMS_DYNAMIC_ENV = "DYNAMIC_ENV"
  APP_PARAMS_PORT = "PORT"

  # Telegram Bot App Params:
  APP_PARAMS_TELEGRAM_BOT_TOKEN="TELEGRAM_BOT_TOKEN"
  APP_PARAMS_TELEGRAM_BOT_NAME="TELEGRAM_BOT_NAME"
  APP_PARAMS_MESSAGE_HANDLER="MESSAGE_HANDLER"
  APP_PARAMS_MESSAGE_HANDLER_ARGS="MESSAGE_HANDLER_ARGS"
  APP_PARAMS_MESSAGE_HANDLER_NAME="MESSAGE_HANDLER_NAME"
  APP_PARAMS_PROCESSING_HANDLER="PROCESSING_HANDLER"
  APP_PARAMS_PROCESSING_HANDLER_ARGS="PROCESSING_HANDLER_ARGS"

  # Custom Code App Params:
  APP_PARAMS_CODE="CODE"

  #########################
  # Auth result keys
  SENDER = "sender"
  SENDER_ORACLES = "sender_oracles"
  SENDER_NODES_COUNT = "sender_nodes_count"
  SENDER_TOTAL_COUNT = "sender_total_count"

class DEEPLOY_STATUS:
  SUCCESS = "success"
  FAIL = "fail"
  ERROR = "error"
  PENDING = "pending"
  TIMEOUT = "timeout"
  COMMAND_DELIVERED = "command_delivered"

class DEEPLOY_ERRORS:
  GENERIC = "ERR01_DEEPLOY_GENERIC_ERROR"
  NODES1 = "ERR02_DEEPLOY_NODES1"
  NODES2 = "ERR03_DEEPLOY_NODES2"
  NODES3 = "ERR04_DEEPLOY_NODES3"
  NODES4 = "ERR05_DEEPLOY_NODES4"
  NODERES1 = "ERR06_DEEPLOY_TARGET_NODE_RESOURCES1"
  PLINST1 = "ERR07_DEEPLOY_PLUGIN_INSTANCE1"
  APP1 = "ERR08_DEEPLOY_APP1"


class DEEPLOY_REQUEST_PATHS:
  CREATE_PIPELINE = "create_pipeline"
  DELETE_PIPELINE = "delete_pipeline"
  GET_APPS = "get_apps"


class DEEPLOY_RESOURCES:
  # Result dictionary keys
  STATUS = 'status'
  DETAILS = 'details'
  AVAILABLE = 'available'
  REQUIRED = 'required'
  
  # Resource types
  CPU = 'CPU'
  MEMORY = 'Memory'
  
  # Units
  CORES = 'cores'
  MB = 'MB'
  
  # Resource keys in app_params
  CONTAINER_RESOURCES = 'CONTAINER_RESOURCES'

  # Default values
  DEFAULT_MEMORY = '512m'
  DEFAULT_CPU = 1

  # Resource detail dictionary keys
  RESOURCE = 'resource'
  AVAILABLE_VALUE = 'available'
  REQUIRED_VALUE = 'required'
  UNIT = 'unit'

class DEFAULT_RESOURCES:
  CPU = 1
  MEMORY = '512m'

class DEEPLOY_PLUGIN_DATA:
  PLUGIN_SIGNATURE = "plugin_signature"
  PLUGIN_INSTANCE = "plugin_instance"
  INSTANCE_ID = "instance_id"
  APP_ID = "app_id"
  NODE = "NODE"

class DEEPLOY_PLUGIN_SIGNATURES:
  CONTAINER_APP_RUNNER = "CONTAINER_APP_RUNNER"

class DEEPLOY_POLICY_VALUES:
  ALWAYS = "always"

DEEPLOY_CREATE_REQUEST = {
  "app_alias" : "some_app_name", 
  "plugin_signature" : "SOME_PLUGIN_01",
  "nonce" : hex(int(time() * 1000)), # recoverable via int(nonce, 16)
  "target_nodes" : [
    "0xai_node_1",
    "0xai_node_2",
  ],
  "target_nodes_count" : 0,
  "node_res_req" : { # this is the resource requirements for the target nodes
      "cpu" : 4,
      "memory" : "16GiB"   
  },
  "app_params" : {
    "IMAGE" : "repo/image:tag",
    "CR_DATA" : {
      "SERVER" : "docker.io",
      "USERNAME" : "user",
      "PASSWORD" : "password",
    },
    "CONTAINER_RESOURCES" : { # this are the resources that will be constrained for the container
      "cpu" : 1,
      "memory" : "512m",
      "ports": {
        "31250": 1849,
        "31251": 80
      }      
    },
    "PORT" : None,
    "NGROK_AUTH_TOKEN" : None,  # put your ngrok API key here
    "NGROK_EDGE_LABEL" : None,  # if we have a already created ngrok edge, we can use it here
    "NGROK_ENABLED" : False, # this tells that the destination plugin instance will USE ngrok
    # TODO: (and observations)
    # - if NGROK_EDGE_LABEL is not None and NGROK_ENABLED is True => normal use
    # - if NGROK_EDGE_LABEL is None and NGROK_ENABLED is True => create/use dynamic url
    # - if NGROK_EDGE_LABEL is not None and NGROK_ENABLED is False => consider NGROK_ENABLED=True
    
    "NGROK_USE_API": True,  # use API or shell for ngrok tunnel creation
    "ENV" : {
      "ENV1" : "value1",
      "ENV2" : "value2",
      "ENV3" : "value3",
      "ENV4" : "value4",
    },
    "DYNAMIC_ENV" : {
      "ENV5" : [
        {
          "type" : "static",
          "value" : "http://"
        },
        {
          "type" : "host_ip",
          "value" : None
        },
        {
          "type" : "static",
          "value" : ":5080/test_api_endpoint"
        }
      ],
      "ENV6" : [
        {
          "type" : "host_ip",
          "value" : "http://"
        }
      ],
    },
    "RESTART_POLICY" : "always",
    "IMAGE_PULL_POLICY" : "always",
    
    
    "OTHER_PARAM1" : "value1",
    "OTHER_PARAM2" : "value2",
    "OTHER_PARAM3" : "value3",
    "OTHER_PARAM4" : "value4",
    "OTHER_PARAM5" : "value5",
  },
  "pipeline_input_type"  : "void",
  "pipeline_input_uri" : None,
  "chainstore_response" : False,
}

###################################################################################################################

DEEPLOY_CREATE_REQUEST_CONTAINER_APP = {
  "app_alias" : "some_app_name", 
  "plugin_signature" : "CONTAINER_APP_RUNNER",
  "nonce" : hex(int(time() * 1000)), # recoverable via int(nonce, 16)
  "target_nodes" : [
    "0xai_node_1",
    "0xai_node_2",
  ],
  "target_nodes_count" : 0,
  "node_res_req" : { # this is the resource requirements for the target nodes
      "cpu" : 4,
      "memory" : "16GiB"   
  },
  "app_params" : {
    "IMAGE" : "repo/image:tag",
    "CR_DATA" : {
      "SERVER" : "docker.io",
      "USERNAME" : "user",
      "PASSWORD" : "password",
    },
    "CONTAINER_RESOURCES" : {
      "cpu" : 1,
      "memory" : "512m"
    },
    "PORT" : None,
    "NGROK_AUTH_TOKEN" : None,  # put your ngrok API key here
    "NGROK_EDGE_LABEL" : None,  # if we have a already created ngrok edge, we can use it here
    "NGROK_ENABLED" : False, # this tells that the destination plugin instance will USE ngrok
    # TODO: (and observations)
    # - if NGROK_EDGE_LABEL is not None and NGROK_ENABLED is True => normal use
    # - if NGROK_EDGE_LABEL is None and NGROK_ENABLED is True => create/use dynamic url
    # - if NGROK_EDGE_LABEL is not None and NGROK_ENABLED is False => consider NGROK_ENABLED=True
    
    "NGROK_USE_API": True,  # use API or shell for ngrok tunnel creation
    "VOLUMES" : {
      "vol1" : "/host/path/vol1",
      "vol2" : "/host/path/vol2",
    },
    "ENV" : {
      "ENV1" : "value1",
      "ENV2" : "value2",
      "ENV3" : "value3",
      "ENV4" : "value4",
    },
    "DYNAMIC_ENV" : {
      "ENV5" : [
        {
          "type" : "static",
          "value" : "http://"
        },
        {
          "type" : "host_ip",
          "value" : None
        },
        {
          "type" : "static",
          "value" : ":5080/test_api_endpoint"
        }
      ],
      "ENV6" : [
        {
          "type" : "host_ip",
          "value" : "http://"
        }
      ],
    },
    "RESTART_POLICY" : "always",
    "IMAGE_PULL_POLICY" : "always",    
  },
  "pipeline_input_type"  : "void", # no other option
  "pipeline_input_uri" : None, # no other option
  "chainstore_response" : True,
}

DEEPLOY_CREATE_REQUEST_SERVICE_APP = {
  "app_alias" : "service_<service>_etc", 
  "plugin_signature" : "CONTAINER_APP_RUNNER",
  "nonce" : hex(int(time() * 1000)), # recoverable via int(nonce, 16)
  "target_nodes" : [
    "0xai_node_1", # always single node for service apps
  ],
  "service_replica" : "0xai_service_replica_1", # this is the service replica name, it will be used to create the service app
  "node_res_req" : { # this is the resource requirements for the target nodes
      "cpu" : 4,
      "memory" : "16GiB"   
  },
  "app_params" : {
    "IMAGE" : "repo/image:tag", # Postgres image or MSSQL image or MySQL image
    "CR_DATA" : {
      "SERVER" : "docker.io",
      "USERNAME" : None,
      "PASSWORD" : None,
    },
    "CONTAINER_RESOURCES" : { # this are the resources that will be constrained for the container
      "cpu" : 2,
      "memory" : "2048m"
    },
    "PORT" : None, # export port 5432 to the host as well as 1433, 3306
    "NGROK_AUTH_TOKEN" : None,  # put your ngrok API key here
    "NGROK_EDGE_LABEL" : None,  # if we have a already created ngrok edge, we can use it here
    "NGROK_ENABLED" : False, # this tells that the destination plugin instance will USE ngrok
    # TODO: (and observations)
    # - if NGROK_EDGE_LABEL is not None and NGROK_ENABLED is True => normal use
    # - if NGROK_EDGE_LABEL is None and NGROK_ENABLED is True => create/use dynamic url
    # - if NGROK_EDGE_LABEL is not None and NGROK_ENABLED is False => consider NGROK_ENABLED=True
    
    "NGROK_USE_API": True,  # use API or shell for ngrok tunnel creation
    "ENV" : {
      "ENV1" : "value1",
      "ENV2" : "value2",
      "ENV3" : "value3",
      "ENV4" : "value4",
    },
    "DYNAMIC_ENV" : {
      "ENV5" : [
        {
          "type" : "static",
          "value" : "http://"
        },
        {
          "type" : "host_ip",
          "value" : None
        },
        {
          "type" : "static",
          "value" : ":5080/test_api_endpoint"
        }
      ],
      "ENV6" : [
        {
          "type" : "host_ip",
          "value" : "http://"
        }
      ],
    },
    "RESTART_POLICY" : "always",
    "IMAGE_PULL_POLICY" : "always"    
  },
  "pipeline_input_type"  : "void",
  "pipeline_input_uri" : None,
  "chainstore_response" : True,
}

DEEPLOY_CREATE_REQUEST_NATIVE_APPS = {
  "app_alias" : "some_app_name", 
  "plugin_signature" : "SOME_PLUGIN_01",
  "nonce" : hex(int(time() * 1000)), # recoverable via int(nonce, 16)
  "target_nodes" : [
    "0xai_node_1",
    "0xai_node_2",
  ],
  "target_nodes_count" : 0,
  "node_res_req" : { # this is the resource requirements for the target nodes
      "cpu" : 4,
      "memory" : "16GiB"   
  },
  "app_params" : {
    "PORT" : None,
    "NGROK_AUTH_TOKEN" : None,  # put your ngrok API key here
    "NGROK_EDGE_LABEL" : None,  # if we have a already created ngrok edge, we can use it here
    "NGROK_ENABLED" : False, # this tells that the destination plugin instance will USE ngrok
    # TODO: (and observations)
    # - if NGROK_EDGE_LABEL is not None and NGROK_ENABLED is True => normal use
    # - if NGROK_EDGE_LABEL is None and NGROK_ENABLED is True => create/use dynamic url
    # - if NGROK_EDGE_LABEL is not None and NGROK_ENABLED is False => consider NGROK_ENABLED=True
    
    "NGROK_USE_API": True,  # use API or shell for ngrok tunnel creation
    "ENV" : {
      "ENV1" : "value1",
      "ENV2" : "value2",
      "ENV3" : "value3",
      "ENV4" : "value4",
    },
    "DYNAMIC_ENV" : {
      "ENV5" : [
        {
          "type" : "static",
          "value" : "http://"
        },
        {
          "type" : "host_ip",
          "value" : None
        },
        {
          "type" : "static",
          "value" : ":5080/test_api_endpoint"
        }
      ],
      "ENV6" : [
        {
          "type" : "host_ip",
          "value" : "http://"
        }
      ],
    },    
    
    "OTHER_PARAM1" : "value1",
    "OTHER_PARAM2" : "value2",
    "OTHER_PARAM3" : "value3",
    "OTHER_PARAM4" : "value4",
    "OTHER_PARAM5" : "value5",
  },
  "pipeline_input_type"  : "void", # DCT
  "pipeline_input_uri" : None, # DCT URL
  "pipeline_params" : {
    "pipeline_input_other1" : "ExampleDatastream", # this will be added to DCT config
    "pipeline_input_other2" : "other param",       # this will be added to DCT config
  },
  "chainstore_response" : False,
}

###################################################################################################################


DEEPLOY_GET_APPS_REQUEST = {
  "nonce" : hex(int(time() * 1000)), # recoverable via int(nonce, 16)
}

DEEPLOY_DELETE_REQUEST = {
  "app_id" : "target_app_name_id_returned_by_get_apps_or_create_pipeline",
  "target_nodes" : [
    "0xai_target_node_1",
    "0xai_target_node_2",
  ],
  "nonce" : hex(int(time() * 1000)), # recoverable via int(nonce, 16)
}  

DEEPLOY_INSTANCE_COMMAND_REQUEST = {
  "app_id" : "target_app_name_id_returned_by_get_apps_or_create_pipeline",
  "target_nodes" : [
    "0xai_target_node_1",
    "0xai_target_node_2",
  ],
  
  "plugin_signature" : "SOME_PLUGIN_01",
  "instance_id" : "SOME_PLUGIN_01_INSTANCE_ID",
  "instance_command" : "RESTART",

  "nonce" : hex(int(time() * 1000)), # recoverable via int(nonce, 16)
}  

DEEPLOY_APP_COMMAND_REQUEST = {
  "app_id" : "target_app_name_id_returned_by_get_apps_or_create_pipeline",
  
  "instance_command" : "RESTART",

  "nonce" : hex(int(time() * 1000)), # recoverable via int(nonce, 16)
}  
