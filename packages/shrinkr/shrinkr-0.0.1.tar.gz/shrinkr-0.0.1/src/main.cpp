#include "compressor.hpp"
#include "compressor_factory.hpp"

#include <cstdint>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <vector>

int main(int argc, char *argv[]) {

  std::vector<std::filesystem::path> inputFiles;
  std::string mode = argv[1];
  int check = 0;

  if (mode == "compress") {
    if (argc < 4) {
      std::cerr << "Usage: " << argv[0]
                << " compress <algorithm> <file1> <file2> ... <fileN>\n"
                   "Available algorithms: \"rle\""
                << std::endl;
      return 1;
    }
    check = 3;
  } else if (mode == "decompress") {
    if (argc < 3) {
      std::cerr << "Usage: " << argv[0] << " decompress <compressed_file>"
                << std::endl;
      return 1;
    }
    check = 2;
  } else {
    std::cerr << "Unknown mode: choose a mode between compresss|decompress."
              << std::endl;
    return 1;
  }

  for (int i = check; i < argc; ++i) {
    if (!(std::filesystem::exists(argv[i]))) {
      std::cerr << "\"" << argv[i] << "\"" << " file doesn't exist."
                << std::endl;
      return 1;
    }
    inputFiles.emplace_back(argv[i]);
  }

  std::ifstream ifs(inputFiles[0], std::ios::binary);
  if (!ifs) {
    std::cerr << "Failed to open file." << std::endl;
    return 1;
  }

  std::unique_ptr<Compressor> compressor;

  if (mode == "compress") {
    std::string algorithm = argv[2];
    compressor = CompressorFactory::create_by_name(algorithm);
    compressor->compress(inputFiles);
  } else if (mode == "decompress") {
    uint8_t firstByte;
    ifs.read(reinterpret_cast<char *>(&firstByte), 1);
    ifs.close();
    try {
      compressor = CompressorFactory::create_by_id(firstByte);
      compressor->decompress(inputFiles);
    } catch (const std::exception &e) {
      std::cerr << e.what() << std::endl;
      return 1;
    }
  } else {
    std::cerr << "Unknown mode: choose a mode between compresss|decompress."
              << std::endl;
    return 1;
  }

  return 0;
}
