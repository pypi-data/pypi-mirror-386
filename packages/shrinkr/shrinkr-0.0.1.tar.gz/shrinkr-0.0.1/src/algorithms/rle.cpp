#include "rle.hpp"
#include "compressor_factory.hpp"
#include "utils.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <string>
#include <vector>

namespace {
bool registered = []() {
  CompressorFactory::register_compressor(
      RLECompressor::ID, RLECompressor::NAME,
      []() { return std::make_unique<RLECompressor>(); });
  return true;
}();
} // namespace

void RLECompressor::compress(const std::vector<std::filesystem::path> &files) {
  std::vector<uint8_t> output;

  // Global header
  uint8_t compression_type = static_cast<uint8_t>(RLECompressor::ID);
  output.push_back(compression_type);

  for (auto &file : files) {
    auto bytes = read_bytes(file);

    if (bytes.empty()) {
      std::cerr << "File " << file << " is empty and couldn't be read."
                << std::endl;
      continue;
    }

    std::vector<uint8_t> compressed_block;
    uint8_t current = bytes[0];
    uint32_t count = 1;

    for (size_t i = 1; i < bytes.size(); i++) {
      if (bytes[i] == current) {
        count++;
      } else {
        compressed_block.push_back(current);
        compressed_block.push_back(count & 0xFF);
        compressed_block.push_back((count >> 8) & 0xFF);
        compressed_block.push_back((count >> 16) & 0xFF);
        compressed_block.push_back((count >> 24) & 0xFF);
        current = bytes[i];
        count = 1;
      }
    }

    compressed_block.push_back(current);
    compressed_block.push_back(count & 0xFF);
    compressed_block.push_back((count >> 8) & 0xFF);
    compressed_block.push_back((count >> 16) & 0xFF);
    compressed_block.push_back((count >> 24) & 0xFF);

    uint32_t block_size = compressed_block.size();

    // File header
    std::string filename_string = file.filename().string();
    output.push_back(static_cast<uint8_t>(filename_string.size()));
    for (auto &character : filename_string) {
      output.push_back(static_cast<uint8_t>(character));
    }

    output.push_back(block_size & 0xFF);
    output.push_back((block_size >> 8) & 0xFF);
    output.push_back((block_size >> 16) & 0xFF);
    output.push_back((block_size >> 24) & 0xFF);

    // Compressed data
    output.insert(output.end(), compressed_block.begin(),
                  compressed_block.end());
  }

  auto compressed_output = files[0];
  compressed_output.replace_extension(".leo");
  write_bytes(compressed_output, output);
}

void RLECompressor::decompress(
    const std::vector<std::filesystem::path> &files) {
  for (auto &file : files) {
    std::ifstream ifs(file, std::ios::binary);

    if (!ifs) {
      std::cerr << "Unable to open the file: " << file << std::endl;
      continue;
    }

    std::vector<uint8_t> data((std::istreambuf_iterator<char>(ifs)),
                              std::istreambuf_iterator<char>());
    size_t index = 1;

    if (index >= data.size()) {
      std::cerr << "File is empty or invalid: " << file << std::endl;
      continue;
    }

    std::filesystem::path dir = file.parent_path() / file.stem();
    std::filesystem::create_directories(dir);

    while (index < data.size()) {
      if (index >= data.size())
        break;

      uint8_t filename_length = data[index++];
      if (index + filename_length > data.size())
        break;

      std::string filename(reinterpret_cast<char *>(&data[index]),
                           filename_length);
      index += filename_length;

      if (index + 4 > data.size())
        break;

      uint32_t block_size = (data[index]) | (data[index + 1] << 8) |
                            (data[index + 2] << 16) | (data[index + 3] << 24);
      index += 4;

      if (index + block_size > data.size())
        break;

      std::vector<uint8_t> compressed_block(data.begin() + index,
                                            data.begin() + index + block_size);

      index += block_size;

      std::vector<uint8_t> output;
      size_t i = 0;
      // value -> 1 byte + count -> 4 bytes = 5 bytes
      while (i + 5 <= compressed_block.size()) {
        uint8_t value = compressed_block[i++];
        uint32_t count = 0;
        count |= compressed_block[i++];
        count |= (compressed_block[i++] << 8);
        count |= (compressed_block[i++] << 16);
        count |= (compressed_block[i++] << 24);

        output.insert(output.end(), count, value);
      }

      std::filesystem::path path = dir / filename;
      write_bytes(path, output);
    }
  }
}
