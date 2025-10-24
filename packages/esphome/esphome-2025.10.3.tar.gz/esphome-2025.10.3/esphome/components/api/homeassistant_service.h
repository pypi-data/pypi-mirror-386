#pragma once

#include "api_server.h"
#ifdef USE_API
#ifdef USE_API_HOMEASSISTANT_SERVICES
#include <functional>
#include <utility>
#include <vector>
#include "api_pb2.h"
#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES_JSON
#include "esphome/components/json/json_util.h"
#endif
#include "esphome/core/automation.h"
#include "esphome/core/helpers.h"

namespace esphome::api {

template<typename... X> class TemplatableStringValue : public TemplatableValue<std::string, X...> {
 private:
  // Helper to convert value to string - handles the case where value is already a string
  template<typename T> static std::string value_to_string(T &&val) { return to_string(std::forward<T>(val)); }

  // Overloads for string types - needed because std::to_string doesn't support them
  static std::string value_to_string(char *val) {
    return val ? std::string(val) : std::string();
  }  // For lambdas returning char* (e.g., itoa)
  static std::string value_to_string(const char *val) { return std::string(val); }  // For lambdas returning .c_str()
  static std::string value_to_string(const std::string &val) { return val; }
  static std::string value_to_string(std::string &&val) { return std::move(val); }

 public:
  TemplatableStringValue() : TemplatableValue<std::string, X...>() {}

  template<typename F, enable_if_t<!is_invocable<F, X...>::value, int> = 0>
  TemplatableStringValue(F value) : TemplatableValue<std::string, X...>(value) {}

  template<typename F, enable_if_t<is_invocable<F, X...>::value, int> = 0>
  TemplatableStringValue(F f)
      : TemplatableValue<std::string, X...>([f](X... x) -> std::string { return value_to_string(f(x...)); }) {}
};

template<typename... Ts> class TemplatableKeyValuePair {
 public:
  // Keys are always string literals from YAML dictionary keys (e.g., "code", "event")
  // and never templatable values or lambdas. Only the value parameter can be a lambda/template.
  // Using pass-by-value with std::move allows optimal performance for both lvalues and rvalues.
  template<typename T> TemplatableKeyValuePair(std::string key, T value) : key(std::move(key)), value(value) {}
  std::string key;
  TemplatableStringValue<Ts...> value;
};

#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES
// Represents the response data from a Home Assistant action
class ActionResponse {
 public:
  ActionResponse(bool success, std::string error_message = "")
      : success_(success), error_message_(std::move(error_message)) {}

#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES_JSON
  ActionResponse(bool success, std::string error_message, const uint8_t *data, size_t data_len)
      : success_(success), error_message_(std::move(error_message)) {
    if (data == nullptr || data_len == 0)
      return;
    this->json_document_ = json::parse_json(data, data_len);
  }
#endif

  bool is_success() const { return this->success_; }
  const std::string &get_error_message() const { return this->error_message_; }

#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES_JSON
  // Get data as parsed JSON object (const version returns read-only view)
  JsonObjectConst get_json() const { return this->json_document_.as<JsonObjectConst>(); }
#endif

 protected:
  bool success_;
  std::string error_message_;
#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES_JSON
  JsonDocument json_document_;
#endif
};

// Callback type for action responses
template<typename... Ts> using ActionResponseCallback = std::function<void(const ActionResponse &, Ts...)>;
#endif

template<typename... Ts> class HomeAssistantServiceCallAction : public Action<Ts...> {
 public:
  explicit HomeAssistantServiceCallAction(APIServer *parent, bool is_event) : parent_(parent) {
    this->flags_.is_event = is_event;
  }

  template<typename T> void set_service(T service) { this->service_ = service; }

  // Keys are always string literals from the Python code generation (e.g., cg.add(var.add_data("tag_id", templ))).
  // The value parameter can be a lambda/template, but keys are never templatable.
  // Using pass-by-value allows the compiler to optimize for both lvalues and rvalues.
  template<typename T> void add_data(std::string key, T value) { this->data_.emplace_back(std::move(key), value); }
  template<typename T> void add_data_template(std::string key, T value) {
    this->data_template_.emplace_back(std::move(key), value);
  }
  template<typename T> void add_variable(std::string key, T value) {
    this->variables_.emplace_back(std::move(key), value);
  }

#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES
  template<typename T> void set_response_template(T response_template) {
    this->response_template_ = response_template;
    this->flags_.has_response_template = true;
  }

  void set_wants_status() { this->flags_.wants_status = true; }
  void set_wants_response() { this->flags_.wants_response = true; }

#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES_JSON
  Trigger<JsonObjectConst, Ts...> *get_success_trigger_with_response() const {
    return this->success_trigger_with_response_;
  }
#endif
  Trigger<Ts...> *get_success_trigger() const { return this->success_trigger_; }
  Trigger<std::string, Ts...> *get_error_trigger() const { return this->error_trigger_; }
#endif  // USE_API_HOMEASSISTANT_ACTION_RESPONSES

  void play(Ts... x) override {
    HomeassistantActionRequest resp;
    std::string service_value = this->service_.value(x...);
    resp.set_service(StringRef(service_value));
    resp.is_event = this->flags_.is_event;
    for (auto &it : this->data_) {
      resp.data.emplace_back();
      auto &kv = resp.data.back();
      kv.set_key(StringRef(it.key));
      kv.value = it.value.value(x...);
    }
    for (auto &it : this->data_template_) {
      resp.data_template.emplace_back();
      auto &kv = resp.data_template.back();
      kv.set_key(StringRef(it.key));
      kv.value = it.value.value(x...);
    }
    for (auto &it : this->variables_) {
      resp.variables.emplace_back();
      auto &kv = resp.variables.back();
      kv.set_key(StringRef(it.key));
      kv.value = it.value.value(x...);
    }

#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES
    if (this->flags_.wants_status) {
      // Generate a unique call ID for this service call
      static uint32_t call_id_counter = 1;
      uint32_t call_id = call_id_counter++;
      resp.call_id = call_id;
#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES_JSON
      if (this->flags_.wants_response) {
        resp.wants_response = true;
        // Set response template if provided
        if (this->flags_.has_response_template) {
          std::string response_template_value = this->response_template_.value(x...);
          resp.response_template = response_template_value;
        }
      }
#endif

      auto captured_args = std::make_tuple(x...);
      this->parent_->register_action_response_callback(call_id, [this, captured_args](const ActionResponse &response) {
        std::apply(
            [this, &response](auto &&...args) {
              if (response.is_success()) {
#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES_JSON
                if (this->flags_.wants_response) {
                  this->success_trigger_with_response_->trigger(response.get_json(), args...);
                } else
#endif
                {
                  this->success_trigger_->trigger(args...);
                }
              } else {
                this->error_trigger_->trigger(response.get_error_message(), args...);
              }
            },
            captured_args);
      });
    }
#endif

    this->parent_->send_homeassistant_action(resp);
  }

 protected:
  APIServer *parent_;
  TemplatableStringValue<Ts...> service_{};
  std::vector<TemplatableKeyValuePair<Ts...>> data_;
  std::vector<TemplatableKeyValuePair<Ts...>> data_template_;
  std::vector<TemplatableKeyValuePair<Ts...>> variables_;
#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES
#ifdef USE_API_HOMEASSISTANT_ACTION_RESPONSES_JSON
  TemplatableStringValue<Ts...> response_template_{""};
  Trigger<JsonObjectConst, Ts...> *success_trigger_with_response_ = new Trigger<JsonObjectConst, Ts...>();
#endif  // USE_API_HOMEASSISTANT_ACTION_RESPONSES_JSON
  Trigger<Ts...> *success_trigger_ = new Trigger<Ts...>();
  Trigger<std::string, Ts...> *error_trigger_ = new Trigger<std::string, Ts...>();
#endif  // USE_API_HOMEASSISTANT_ACTION_RESPONSES

  struct Flags {
    uint8_t is_event : 1;
    uint8_t wants_status : 1;
    uint8_t wants_response : 1;
    uint8_t has_response_template : 1;
    uint8_t reserved : 5;
  } flags_{0};
};

}  // namespace esphome::api

#endif
#endif
