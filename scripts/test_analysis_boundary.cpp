#include "analysis.hpp"
#include <cstring>
#include <stdexcept>
#include <cstdio>

int main() {
    constexpr std::uint32_t base = 0x180000;
    const std::uint32_t words[]{0x1000ffff, 0};
    std::vector<std::uint8_t> truncated(4), complete(8);
    std::memcpy(truncated.data(), words, 4);
    std::memcpy(complete.data(), words, 8);
    auto short_image = recomp::Image::raw(base, truncated, {base, base + 4});
    auto long_image = recomp::Image::raw(base, complete, {base, base + 8});
    if (recomp::analyse(short_image, {base}).is_code(base))
        throw std::runtime_error("must not translate a branch without its delay slot");
    if (!recomp::analyse(long_image, {base}).is_code(base))
        throw std::runtime_error("complete branch and slot should translate");
    const std::uint32_t mixed[]{0x03e00008, 0, base + 16, 0, 0x03e00008, 0};
    std::vector<std::uint8_t> bytes(sizeof mixed);
    std::memcpy(bytes.data(), mixed, sizeof mixed);
    auto heap = recomp::Image::raw(base, bytes, {base, base + sizeof mixed});
    if (recomp::analyse(heap, {base}, {}, false).is_code(base + 16))
        throw std::runtime_error("flow-only mode must not infer code from an unrelated heap pointer");
    if (!recomp::analyse(heap, {base}).is_code(base + 16))
        throw std::runtime_error("default ELF discovery should still follow plausible function pointers");
    std::puts("PASS: truncated branch deferred; complete branch translated");
}
