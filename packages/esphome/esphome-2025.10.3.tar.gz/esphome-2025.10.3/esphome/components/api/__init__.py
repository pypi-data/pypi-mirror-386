import base64
import logging

from esphome import automation
from esphome.automation import Condition
import esphome.codegen as cg
from esphome.config_helpers import get_logger_level
import esphome.config_validation as cv
from esphome.const import (
    CONF_ACTION,
    CONF_ACTIONS,
    CONF_CAPTURE_RESPONSE,
    CONF_DATA,
    CONF_DATA_TEMPLATE,
    CONF_EVENT,
    CONF_ID,
    CONF_KEY,
    CONF_MAX_CONNECTIONS,
    CONF_ON_CLIENT_CONNECTED,
    CONF_ON_CLIENT_DISCONNECTED,
    CONF_ON_ERROR,
    CONF_ON_SUCCESS,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_REBOOT_TIMEOUT,
    CONF_RESPONSE_TEMPLATE,
    CONF_SERVICE,
    CONF_SERVICES,
    CONF_TAG,
    CONF_TRIGGER_ID,
    CONF_VARIABLES,
)
from esphome.core import CORE, ID, CoroPriority, coroutine_with_priority
from esphome.cpp_generator import TemplateArgsType
from esphome.types import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "api"
DEPENDENCIES = ["network"]
CODEOWNERS = ["@esphome/core"]


def AUTO_LOAD(config: ConfigType) -> list[str]:
    """Conditionally auto-load json only when capture_response is used."""
    base = ["socket"]

    # Check if any homeassistant.action/homeassistant.service has capture_response: true
    # This flag is set during config validation in _validate_response_config
    if not config or CORE.data.get(DOMAIN, {}).get(CONF_CAPTURE_RESPONSE, False):
        return base + ["json"]

    return base


api_ns = cg.esphome_ns.namespace("api")
APIServer = api_ns.class_("APIServer", cg.Component, cg.Controller)
HomeAssistantServiceCallAction = api_ns.class_(
    "HomeAssistantServiceCallAction", automation.Action
)
ActionResponse = api_ns.class_("ActionResponse")
HomeAssistantActionResponseTrigger = api_ns.class_(
    "HomeAssistantActionResponseTrigger", automation.Trigger
)
APIConnectedCondition = api_ns.class_("APIConnectedCondition", Condition)

UserServiceTrigger = api_ns.class_("UserServiceTrigger", automation.Trigger)
ListEntitiesServicesArgument = api_ns.class_("ListEntitiesServicesArgument")
SERVICE_ARG_NATIVE_TYPES = {
    "bool": bool,
    "int": cg.int32,
    "float": float,
    "string": cg.std_string,
    "bool[]": cg.std_vector.template(bool),
    "int[]": cg.std_vector.template(cg.int32),
    "float[]": cg.std_vector.template(float),
    "string[]": cg.std_vector.template(cg.std_string),
}
CONF_ENCRYPTION = "encryption"
CONF_BATCH_DELAY = "batch_delay"
CONF_CUSTOM_SERVICES = "custom_services"
CONF_HOMEASSISTANT_SERVICES = "homeassistant_services"
CONF_HOMEASSISTANT_STATES = "homeassistant_states"
CONF_LISTEN_BACKLOG = "listen_backlog"
CONF_MAX_SEND_QUEUE = "max_send_queue"


def validate_encryption_key(value):
    value = cv.string_strict(value)
    try:
        decoded = base64.b64decode(value, validate=True)
    except ValueError as err:
        raise cv.Invalid("Invalid key format, please check it's using base64") from err

    if len(decoded) != 32:
        raise cv.Invalid("Encryption key must be base64 and 32 bytes long")

    # Return original data for roundtrip conversion
    return value


ACTIONS_SCHEMA = automation.validate_automation(
    {
        cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(UserServiceTrigger),
        cv.Exclusive(CONF_SERVICE, group_of_exclusion=CONF_ACTION): cv.valid_name,
        cv.Exclusive(CONF_ACTION, group_of_exclusion=CONF_ACTION): cv.valid_name,
        cv.Optional(CONF_VARIABLES, default={}): cv.Schema(
            {
                cv.validate_id_name: cv.one_of(*SERVICE_ARG_NATIVE_TYPES, lower=True),
            }
        ),
    },
    cv.All(
        cv.has_exactly_one_key(CONF_SERVICE, CONF_ACTION),
        cv.rename_key(CONF_SERVICE, CONF_ACTION),
    ),
)

ENCRYPTION_SCHEMA = cv.Schema(
    {
        cv.Optional(CONF_KEY): validate_encryption_key,
    }
)


def _encryption_schema(config):
    if config is None:
        config = {}
    return ENCRYPTION_SCHEMA(config)


def _validate_api_config(config: ConfigType) -> ConfigType:
    """Validate API configuration with mutual exclusivity check and deprecation warning."""
    # Check if both password and encryption are configured
    has_password = CONF_PASSWORD in config and config[CONF_PASSWORD]
    has_encryption = CONF_ENCRYPTION in config

    if has_password and has_encryption:
        raise cv.Invalid(
            "The 'password' and 'encryption' options are mutually exclusive. "
            "The API client only supports one authentication method at a time. "
            "Please remove one of them. "
            "Note: 'password' authentication is deprecated and will be removed in version 2026.1.0. "
            "We strongly recommend using 'encryption' instead for better security."
        )

    # Warn about password deprecation
    if has_password:
        _LOGGER.warning(
            "API 'password' authentication has been deprecated since May 2022 and will be removed in version 2026.1.0. "
            "Please migrate to the 'encryption' configuration. "
            "See https://esphome.io/components/api.html#configuration-variables"
        )

    return config


CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(APIServer),
            cv.Optional(CONF_PORT, default=6053): cv.port,
            cv.Optional(CONF_PASSWORD, default=""): cv.string_strict,
            cv.Optional(
                CONF_REBOOT_TIMEOUT, default="15min"
            ): cv.positive_time_period_milliseconds,
            cv.Exclusive(
                CONF_SERVICES, group_of_exclusion=CONF_ACTIONS
            ): ACTIONS_SCHEMA,
            cv.Exclusive(CONF_ACTIONS, group_of_exclusion=CONF_ACTIONS): ACTIONS_SCHEMA,
            cv.Optional(CONF_ENCRYPTION): _encryption_schema,
            cv.Optional(CONF_BATCH_DELAY, default="100ms"): cv.All(
                cv.positive_time_period_milliseconds,
                cv.Range(max=cv.TimePeriod(milliseconds=65535)),
            ),
            cv.Optional(CONF_CUSTOM_SERVICES, default=False): cv.boolean,
            cv.Optional(CONF_HOMEASSISTANT_SERVICES, default=False): cv.boolean,
            cv.Optional(CONF_HOMEASSISTANT_STATES, default=False): cv.boolean,
            cv.Optional(CONF_ON_CLIENT_CONNECTED): automation.validate_automation(
                single=True
            ),
            cv.Optional(CONF_ON_CLIENT_DISCONNECTED): automation.validate_automation(
                single=True
            ),
            # Connection limits to prevent memory exhaustion on resource-constrained devices
            # Each connection uses ~500-1000 bytes of RAM plus system resources
            # Platform defaults based on available RAM and network stack implementation:
            cv.SplitDefault(
                CONF_LISTEN_BACKLOG,
                esp8266=1,  # Limited RAM (~40KB free), LWIP raw sockets
                esp32=4,  # More RAM (520KB), BSD sockets
                rp2040=1,  # Limited RAM (264KB), LWIP raw sockets like ESP8266
                bk72xx=4,  # Moderate RAM, BSD-style sockets
                rtl87xx=4,  # Moderate RAM, BSD-style sockets
                host=4,  # Abundant resources
                ln882x=4,  # Moderate RAM
            ): cv.int_range(min=1, max=10),
            cv.SplitDefault(
                CONF_MAX_CONNECTIONS,
                esp8266=4,  # ~40KB free RAM, each connection uses ~500-1000 bytes
                esp32=8,  # 520KB RAM available
                rp2040=4,  # 264KB RAM but LWIP constraints
                bk72xx=8,  # Moderate RAM
                rtl87xx=8,  # Moderate RAM
                host=8,  # Abundant resources
                ln882x=8,  # Moderate RAM
            ): cv.int_range(min=1, max=20),
            # Maximum queued send buffers per connection before dropping connection
            # Each buffer uses ~8-12 bytes overhead plus actual message size
            # Platform defaults based on available RAM and typical message rates:
            cv.SplitDefault(
                CONF_MAX_SEND_QUEUE,
                esp8266=5,  # Limited RAM, need to fail fast
                esp32=8,  # More RAM, can buffer more
                rp2040=5,  # Limited RAM
                bk72xx=8,  # Moderate RAM
                rtl87xx=8,  # Moderate RAM
                host=16,  # Abundant resources
                ln882x=8,  # Moderate RAM
            ): cv.int_range(min=1, max=64),
        }
    ).extend(cv.COMPONENT_SCHEMA),
    cv.rename_key(CONF_SERVICES, CONF_ACTIONS),
    _validate_api_config,
)


@coroutine_with_priority(CoroPriority.WEB)
async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    cg.add(var.set_port(config[CONF_PORT]))
    if config[CONF_PASSWORD]:
        cg.add_define("USE_API_PASSWORD")
        cg.add(var.set_password(config[CONF_PASSWORD]))
    cg.add(var.set_reboot_timeout(config[CONF_REBOOT_TIMEOUT]))
    cg.add(var.set_batch_delay(config[CONF_BATCH_DELAY]))
    if CONF_LISTEN_BACKLOG in config:
        cg.add(var.set_listen_backlog(config[CONF_LISTEN_BACKLOG]))
    if CONF_MAX_CONNECTIONS in config:
        cg.add(var.set_max_connections(config[CONF_MAX_CONNECTIONS]))
    cg.add_define("API_MAX_SEND_QUEUE", config[CONF_MAX_SEND_QUEUE])

    # Set USE_API_SERVICES if any services are enabled
    if config.get(CONF_ACTIONS) or config[CONF_CUSTOM_SERVICES]:
        cg.add_define("USE_API_SERVICES")

    if config[CONF_HOMEASSISTANT_SERVICES]:
        cg.add_define("USE_API_HOMEASSISTANT_SERVICES")

    if config[CONF_HOMEASSISTANT_STATES]:
        cg.add_define("USE_API_HOMEASSISTANT_STATES")

    if actions := config.get(CONF_ACTIONS, []):
        for conf in actions:
            template_args = []
            func_args = []
            service_arg_names = []
            for name, var_ in conf[CONF_VARIABLES].items():
                native = SERVICE_ARG_NATIVE_TYPES[var_]
                template_args.append(native)
                func_args.append((native, name))
                service_arg_names.append(name)
            templ = cg.TemplateArguments(*template_args)
            trigger = cg.new_Pvariable(
                conf[CONF_TRIGGER_ID], templ, conf[CONF_ACTION], service_arg_names
            )
            cg.add(var.register_user_service(trigger))
            await automation.build_automation(trigger, func_args, conf)

    if CONF_ON_CLIENT_CONNECTED in config:
        cg.add_define("USE_API_CLIENT_CONNECTED_TRIGGER")
        await automation.build_automation(
            var.get_client_connected_trigger(),
            [(cg.std_string, "client_info"), (cg.std_string, "client_address")],
            config[CONF_ON_CLIENT_CONNECTED],
        )

    if CONF_ON_CLIENT_DISCONNECTED in config:
        cg.add_define("USE_API_CLIENT_DISCONNECTED_TRIGGER")
        await automation.build_automation(
            var.get_client_disconnected_trigger(),
            [(cg.std_string, "client_info"), (cg.std_string, "client_address")],
            config[CONF_ON_CLIENT_DISCONNECTED],
        )

    if (encryption_config := config.get(CONF_ENCRYPTION, None)) is not None:
        if key := encryption_config.get(CONF_KEY):
            decoded = base64.b64decode(key)
            cg.add(var.set_noise_psk(list(decoded)))
            cg.add_define("USE_API_NOISE_PSK_FROM_YAML")
        else:
            # No key provided, but encryption desired
            # This will allow a plaintext client to provide a noise key,
            # send it to the device, and then switch to noise.
            # The key will be saved in flash and used for future connections
            # and plaintext disabled. Only a factory reset can remove it.
            cg.add_define("USE_API_PLAINTEXT")
        cg.add_define("USE_API_NOISE")
        cg.add_library("esphome/noise-c", "0.1.10")
    else:
        cg.add_define("USE_API_PLAINTEXT")

    cg.add_define("USE_API")
    cg.add_global(api_ns.using)


KEY_VALUE_SCHEMA = cv.Schema({cv.string: cv.templatable(cv.string_strict)})


def _validate_response_config(config: ConfigType) -> ConfigType:
    # Validate dependencies:
    # - response_template requires capture_response: true
    # - capture_response: true requires on_success
    if CONF_RESPONSE_TEMPLATE in config and not config[CONF_CAPTURE_RESPONSE]:
        raise cv.Invalid(
            f"`{CONF_RESPONSE_TEMPLATE}` requires `{CONF_CAPTURE_RESPONSE}: true` to be set.",
            path=[CONF_RESPONSE_TEMPLATE],
        )

    if config[CONF_CAPTURE_RESPONSE] and CONF_ON_SUCCESS not in config:
        raise cv.Invalid(
            f"`{CONF_CAPTURE_RESPONSE}: true` requires `{CONF_ON_SUCCESS}` to be set.",
            path=[CONF_CAPTURE_RESPONSE],
        )

    # Track if any action uses capture_response for AUTO_LOAD
    if config[CONF_CAPTURE_RESPONSE]:
        CORE.data.setdefault(DOMAIN, {})[CONF_CAPTURE_RESPONSE] = True

    return config


HOMEASSISTANT_ACTION_ACTION_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.use_id(APIServer),
            cv.Exclusive(CONF_SERVICE, group_of_exclusion=CONF_ACTION): cv.templatable(
                cv.string
            ),
            cv.Exclusive(CONF_ACTION, group_of_exclusion=CONF_ACTION): cv.templatable(
                cv.string
            ),
            cv.Optional(CONF_DATA, default={}): KEY_VALUE_SCHEMA,
            cv.Optional(CONF_DATA_TEMPLATE, default={}): KEY_VALUE_SCHEMA,
            cv.Optional(CONF_VARIABLES, default={}): cv.Schema(
                {cv.string: cv.returning_lambda}
            ),
            cv.Optional(CONF_RESPONSE_TEMPLATE): cv.templatable(cv.string),
            cv.Optional(CONF_CAPTURE_RESPONSE, default=False): cv.boolean,
            cv.Optional(CONF_ON_SUCCESS): automation.validate_automation(single=True),
            cv.Optional(CONF_ON_ERROR): automation.validate_automation(single=True),
        }
    ),
    cv.has_exactly_one_key(CONF_SERVICE, CONF_ACTION),
    cv.rename_key(CONF_SERVICE, CONF_ACTION),
    _validate_response_config,
)


@automation.register_action(
    "homeassistant.action",
    HomeAssistantServiceCallAction,
    HOMEASSISTANT_ACTION_ACTION_SCHEMA,
)
@automation.register_action(
    "homeassistant.service",
    HomeAssistantServiceCallAction,
    HOMEASSISTANT_ACTION_ACTION_SCHEMA,
)
async def homeassistant_service_to_code(
    config: ConfigType,
    action_id: ID,
    template_arg: cg.TemplateArguments,
    args: TemplateArgsType,
):
    cg.add_define("USE_API_HOMEASSISTANT_SERVICES")
    serv = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, serv, False)
    templ = await cg.templatable(config[CONF_ACTION], args, None)
    cg.add(var.set_service(templ))
    for key, value in config[CONF_DATA].items():
        templ = await cg.templatable(value, args, None)
        cg.add(var.add_data(key, templ))
    for key, value in config[CONF_DATA_TEMPLATE].items():
        templ = await cg.templatable(value, args, None)
        cg.add(var.add_data_template(key, templ))
    for key, value in config[CONF_VARIABLES].items():
        templ = await cg.templatable(value, args, None)
        cg.add(var.add_variable(key, templ))

    if on_error := config.get(CONF_ON_ERROR):
        cg.add_define("USE_API_HOMEASSISTANT_ACTION_RESPONSES")
        cg.add_define("USE_API_HOMEASSISTANT_ACTION_RESPONSES_ERRORS")
        cg.add(var.set_wants_status())
        await automation.build_automation(
            var.get_error_trigger(),
            [(cg.std_string, "error"), *args],
            on_error,
        )

    if on_success := config.get(CONF_ON_SUCCESS):
        cg.add_define("USE_API_HOMEASSISTANT_ACTION_RESPONSES")
        cg.add(var.set_wants_status())
        if config[CONF_CAPTURE_RESPONSE]:
            cg.add(var.set_wants_response())
            cg.add_define("USE_API_HOMEASSISTANT_ACTION_RESPONSES_JSON")
            await automation.build_automation(
                var.get_success_trigger_with_response(),
                [(cg.JsonObjectConst, "response"), *args],
                on_success,
            )

            if response_template := config.get(CONF_RESPONSE_TEMPLATE):
                templ = await cg.templatable(response_template, args, cg.std_string)
                cg.add(var.set_response_template(templ))

        else:
            await automation.build_automation(
                var.get_success_trigger(),
                args,
                on_success,
            )

    return var


def validate_homeassistant_event(value):
    value = cv.string(value)
    if not value.startswith("esphome."):
        raise cv.Invalid(
            "ESPHome can only generate Home Assistant events that begin with "
            "esphome. For example 'esphome.xyz'"
        )
    return value


HOMEASSISTANT_EVENT_ACTION_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.use_id(APIServer),
        cv.Required(CONF_EVENT): validate_homeassistant_event,
        cv.Optional(CONF_DATA, default={}): KEY_VALUE_SCHEMA,
        cv.Optional(CONF_DATA_TEMPLATE, default={}): KEY_VALUE_SCHEMA,
        cv.Optional(CONF_VARIABLES, default={}): KEY_VALUE_SCHEMA,
    }
)


@automation.register_action(
    "homeassistant.event",
    HomeAssistantServiceCallAction,
    HOMEASSISTANT_EVENT_ACTION_SCHEMA,
)
async def homeassistant_event_to_code(config, action_id, template_arg, args):
    cg.add_define("USE_API_HOMEASSISTANT_SERVICES")
    serv = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, serv, True)
    templ = await cg.templatable(config[CONF_EVENT], args, None)
    cg.add(var.set_service(templ))
    for key, value in config[CONF_DATA].items():
        templ = await cg.templatable(value, args, None)
        cg.add(var.add_data(key, templ))
    for key, value in config[CONF_DATA_TEMPLATE].items():
        templ = await cg.templatable(value, args, None)
        cg.add(var.add_data_template(key, templ))
    for key, value in config[CONF_VARIABLES].items():
        templ = await cg.templatable(value, args, None)
        cg.add(var.add_variable(key, templ))
    return var


HOMEASSISTANT_TAG_SCANNED_ACTION_SCHEMA = cv.maybe_simple_value(
    {
        cv.GenerateID(): cv.use_id(APIServer),
        cv.Required(CONF_TAG): cv.templatable(cv.string_strict),
    },
    key=CONF_TAG,
)


@automation.register_action(
    "homeassistant.tag_scanned",
    HomeAssistantServiceCallAction,
    HOMEASSISTANT_TAG_SCANNED_ACTION_SCHEMA,
)
async def homeassistant_tag_scanned_to_code(config, action_id, template_arg, args):
    cg.add_define("USE_API_HOMEASSISTANT_SERVICES")
    serv = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, serv, True)
    cg.add(var.set_service("esphome.tag_scanned"))
    templ = await cg.templatable(config[CONF_TAG], args, cg.std_string)
    cg.add(var.add_data("tag_id", templ))
    return var


@automation.register_condition("api.connected", APIConnectedCondition, {})
async def api_connected_to_code(config, condition_id, template_arg, args):
    return cg.new_Pvariable(condition_id, template_arg)


def FILTER_SOURCE_FILES() -> list[str]:
    """Filter out api_pb2_dump.cpp when proto message dumping is not enabled,
    user_services.cpp when no services are defined, and protocol-specific
    implementations based on encryption configuration."""
    files_to_filter: list[str] = []

    # api_pb2_dump.cpp is only needed when HAS_PROTO_MESSAGE_DUMP is defined
    # This is a particularly large file that still needs to be opened and read
    # all the way to the end even when ifdef'd out
    #
    # HAS_PROTO_MESSAGE_DUMP is defined when ESPHOME_LOG_HAS_VERY_VERBOSE is set,
    # which happens when the logger level is VERY_VERBOSE
    if get_logger_level() != "VERY_VERBOSE":
        files_to_filter.append("api_pb2_dump.cpp")

    # user_services.cpp is only needed when services are defined
    config = CORE.config.get(DOMAIN, {})
    if config and not config.get(CONF_ACTIONS) and not config[CONF_CUSTOM_SERVICES]:
        files_to_filter.append("user_services.cpp")

    # Filter protocol-specific implementations based on encryption configuration
    encryption_config = config.get(CONF_ENCRYPTION) if config else None

    # If encryption is not configured at all, we only need plaintext
    if encryption_config is None:
        files_to_filter.append("api_frame_helper_noise.cpp")
    # If encryption is configured with a key, we only need noise
    elif encryption_config.get(CONF_KEY):
        files_to_filter.append("api_frame_helper_plaintext.cpp")
    # If encryption is configured but no key is provided, we need both
    # (this allows a plaintext client to provide a noise key)

    return files_to_filter
