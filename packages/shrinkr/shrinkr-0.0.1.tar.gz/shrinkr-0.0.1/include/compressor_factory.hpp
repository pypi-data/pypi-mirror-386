#pragma once
#include "compressor.hpp"
#include <cstdint>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>

class CompressorFactory {
public:
  using Creator = std::function<std::unique_ptr<Compressor>()>;

  static void register_compressor(uint8_t id, const std::string &name,
                                  Creator creator) {
    get_by_id()[id] = creator;
    get_by_name()[name] = creator;
  }

  static std::unique_ptr<Compressor> create_by_id(uint8_t id) {
    auto it = get_by_id().find(id);
    if (it == get_by_id().end())
      throw std::invalid_argument("Unknown compressor ID: " +
                                  std::to_string(id));
    return it->second();
  }

  static std::unique_ptr<Compressor> create_by_name(const std::string &name) {
    auto it = get_by_name().find(name);
    if (it == get_by_name().end())
      throw std::invalid_argument("Unknown compressor name: " + name);
    return it->second();
  }

private:
  static std::unordered_map<uint8_t, Creator> &get_by_id() {
    static std::unordered_map<uint8_t, Creator> by_id;
    return by_id;
  }
  static std::unordered_map<std::string, Creator> &get_by_name() {
    static std::unordered_map<std::string, Creator> by_name;
    return by_name;
  }
};
