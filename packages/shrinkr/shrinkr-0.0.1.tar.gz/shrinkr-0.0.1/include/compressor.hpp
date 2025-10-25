#pragma once
#include <filesystem>
#include <vector>

class Compressor {
public:
  virtual void compress(const std::vector<std::filesystem::path> &files) = 0;
  virtual void decompress(const std::vector<std::filesystem::path> &files) = 0;
  virtual ~Compressor() = default;
};
