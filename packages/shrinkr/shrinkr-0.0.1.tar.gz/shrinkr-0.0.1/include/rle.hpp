#pragma once
#include "compressor.hpp"
#include <cstdint>
#include <filesystem>
#include <vector>

class RLECompressor : public Compressor {
public:
  static constexpr uint8_t ID = 1;
  static constexpr const char *NAME = "rle";

  void compress(const std::vector<std::filesystem::path> &files) override;
  void decompress(const std::vector<std::filesystem::path> &files) override;
};
