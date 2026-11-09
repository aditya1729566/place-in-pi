#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

using Clock = std::chrono::steady_clock;
struct Shard { const char* data; size_t size; uint64_t start; };

std::vector<std::string> split(const std::string& line) {
  std::vector<std::string> fields;
  std::stringstream stream(line);
  std::string field;
  while (std::getline(stream, field, '\t')) fields.push_back(field);
  return fields;
}

uint64_t number(const std::string& value) {
  if (value.empty() || !std::all_of(value.begin(), value.end(), [](char c) { return c >= '0' && c <= '9'; }))
    throw std::invalid_argument("invalid number");
  size_t end = 0;
  auto result = std::stoull(value, &end);
  if (end != value.size()) throw std::invalid_argument("invalid number");
  return result;
}

int main(int argc, char** argv) {
  if (argc < 2) { std::cerr << "usage: pi_search SHARD_FILE...\n"; return 2; }
  std::vector<Shard> shards;
  uint64_t total = 0;
  for (int arg = 1; arg < argc; ++arg) {
    int fd = open(argv[arg], O_RDONLY);
    if (fd < 0) { std::cerr << "cannot open shard\n"; return 2; }
    struct stat stats {};
    if (fstat(fd, &stats) != 0 || stats.st_size <= 0) { std::cerr << "invalid shard size\n"; close(fd); return 2; }
    size_t size = static_cast<size_t>(stats.st_size);
    auto data = static_cast<const char*>(mmap(nullptr, size, PROT_READ, MAP_PRIVATE, fd, 0));
    close(fd);
    if (data == MAP_FAILED) { std::cerr << "cannot map shard\n"; return 2; }
    shards.push_back({data, size, total});
    total += size;
  }
  if (shards.front().data[0] != '1') { std::cerr << "invalid corpus prefix\n"; return 2; }
  std::string line;
  while (std::getline(std::cin, line)) {
    try {
      auto f = split(line);
      if (f.size() == 5 && f[0] == "SCAN") {
        const auto& pattern = f[1];
        if (pattern.empty() || pattern.size() > 384 || !std::all_of(pattern.begin(), pattern.end(), [](char c) { return c >= '0' && c <= '9'; }))
          throw std::invalid_argument("invalid pattern");
        uint64_t offset = number(f[2]), limit = number(f[3]), timeout = number(f[4]);
        if (limit < 1 || limit > 100 || timeout < 1 || timeout > 120000) throw std::invalid_argument("invalid bounds");
        std::vector<size_t> failure(pattern.size());
        for (size_t i = 1, j = 0; i < pattern.size(); ++i) {
          while (j && pattern[i] != pattern[j]) j = failure[j - 1];
          if (pattern[i] == pattern[j]) ++j;
          failure[i] = j;
        }
        auto began = Clock::now();
        uint64_t scanned = 0, matches = 0, first = 0;
        bool complete = true;
        size_t j = 0;
        std::vector<uint64_t> page;
        for (const auto& shard : shards) {
          for (size_t i = 0; i < shard.size; ++i) {
            if ((scanned & 65535) == 0 && scanned && std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - began).count() >= static_cast<int64_t>(timeout)) {
              complete = false; break;
            }
            char digit = shard.data[i];
            if (digit < '0' || digit > '9') throw std::invalid_argument("corpus contains non-decimal content");
            while (j && digit != pattern[j]) j = failure[j - 1];
            if (digit == pattern[j]) ++j;
            if (j == pattern.size()) {
              uint64_t position = scanned + 2 - pattern.size();
              if (!first) first = position;
              if (matches >= offset && page.size() < limit) page.push_back(position);
              ++matches;
              j = failure[j - 1];
            }
            ++scanned;
          }
          if (!complete) break;
        }
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - began).count();
        std::cout << "SCAN\t" << (complete ? "1" : "0") << '\t' << matches << '\t' << first << '\t' << elapsed << '\t';
        for (size_t i = 0; i < page.size(); ++i) { if (i) std::cout << ','; std::cout << page[i]; }
        std::cout << '\n' << std::flush;
      } else if (f.size() == 3 && f[0] == "DIGITS") {
        uint64_t start = number(f[1]), count = number(f[2]);
        if (start < 1 || count < 1 || count > 4096 || start > total || count > total - start + 1)
          throw std::invalid_argument("invalid digit window");
        std::string output;
        output.reserve(count);
        uint64_t zero_start = start - 1;
        for (const auto& shard : shards) {
          if (zero_start >= shard.start + shard.size || zero_start + count <= shard.start) continue;
          uint64_t local_start = std::max(zero_start, shard.start) - shard.start;
          uint64_t local_end = std::min(zero_start + count, shard.start + shard.size) - shard.start;
          output.append(shard.data + local_start, local_end - local_start);
        }
        std::cout << "DIGITS\t" << output << '\n' << std::flush;
      } else if (f.size() == 1 && f[0] == "PING") {
        std::cout << "PONG\t" << total << '\n' << std::flush;
      } else throw std::invalid_argument("invalid command");
    } catch (const std::exception& error) {
      std::cout << "ERROR\t" << error.what() << '\n' << std::flush;
    }
  }
  for (const auto& shard : shards) munmap(const_cast<char*>(shard.data), shard.size);
}
