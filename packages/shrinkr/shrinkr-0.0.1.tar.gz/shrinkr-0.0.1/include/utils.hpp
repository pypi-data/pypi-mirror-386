#pragma once
#include <cstdint>
#include <filesystem>
#include <vector>

std::vector<uint8_t> read_bytes(const std::filesystem::path &path);

void write_bytes(const std::filesystem::path &path,
                 const std::vector<uint8_t> &data);
