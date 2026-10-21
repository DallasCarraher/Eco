#include "dmac.hpp"
#include "ps2/memory.hpp"
#include <cstdio>
#include <cstring>
#include <initializer_list>
#include <stdexcept>

int main() {
    using namespace ps2;
    constexpr std::uint32_t chain = 0x20000, payload = 0x20100;
    const std::uint32_t ref[]{0x30000001, payload, 0x11223344, 0x55667788};
    const std::uint32_t end[]{0x70000000, 0, 0x99aabbcc, 0xddeeff00};
    const std::uint32_t data[]{1, 2, 3, 4};
    std::memcpy(g_ram + chain, ref, 16);
    std::memcpy(g_ram + chain + 16, end, 16);
    std::memcpy(g_ram + payload, data, 16);
    for (const bool tte : {false, true}) {
        dmac::reset();
        std::memset(g_spr, 0, kScratchpadSize);
        dmac::write(0x1000d480, 0x3ff0);
        dmac::write(0x1000d430, chain);
        dmac::write(0x1000d400, tte ? 0x144 : 0x104);
        if (tte) {
            if (std::memcmp(g_spr + 0x3ff0, ref, 16) || std::memcmp(g_spr, data, 16) ||
                std::memcmp(g_spr + 16, end, 16) || dmac::read(0x1000d480) != 32)
                throw std::runtime_error("toSPR TTE must copy complete tags and payload, wrapping scratchpad");
        } else if (std::memcmp(g_spr + 0x3ff0, data, 16) || dmac::read(0x1000d480) != 0) {
            throw std::runtime_error("without TTE, only payload must transfer");
        }
    }
    std::puts("PASS: toSPR chain tags, payload, TTE off, and scratchpad wrapping");
}
