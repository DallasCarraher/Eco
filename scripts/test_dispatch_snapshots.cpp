// Exercise production dispatch with overlapping snapshots containing different
// compiled entries. The stubs avoid starting any console devices or GPU.
#include "ps2/generated.hpp"
#include "ps2/system.hpp"
#include <cstdio>
#include <cstdlib>
#include <stdexcept>

namespace ps2 {
alignas(64) std::uint8_t g_ram[kRamSize + 64]{};
alignas(64) std::uint8_t g_spr[kScratchpadSize]{};
Options g_options;
std::uint32_t slow_ld32(std::uint32_t) { throw std::runtime_error("unexpected device access"); }
void halt(const std::string &reason) { throw std::runtime_error(reason); }
}

void check(bool ok, const char *message) {
    if (!ok) throw std::runtime_error(message);
}

void first(ps2::Cpu &c, std::uint32_t, std::uint32_t) { c.r[2].w[0] = 1; }
void second(ps2::Cpu &c, std::uint32_t, std::uint32_t) { c.r[2].w[0] = 2; }

int main() {
    using namespace ps2;
    setenv("PS2_WINDOW_FULL", "1", 1);
    constexpr std::uint32_t base = 0x180000;
    const std::uint32_t words[]{0x12345678, 0x87654321, 0, 0};
    std::memcpy(g_ram + base, words, sizeof words);
    const std::uint16_t entries_a[]{1, 0, 0, 0};
    const std::uint16_t entries_b[]{0, 1, 0, 0};
    const UnitInfo units_a[]{ {0, 16, first, entries_a} };
    const UnitInfo units_b[]{ {0, 16, second, entries_b} };
    const std::uint32_t checks_a[]{0, words[0]};
    const std::uint32_t checks_b[]{4, words[1]};
    const ModuleInfo modules[]{
        {"older", base, 16, checks_a, 1, units_a, 1},
        {"newer", base, 16, checks_b, 1, units_b, 1},
    };
    register_modules(modules, 2);
    check(has_code(base), "first entry should exist");
    check(has_code(base + 4), "later snapshot must not be shadowed by an earlier matching snapshot");
    Cpu c{};
    c.pc = base;
    dispatch(c, 0, 0);
    check(c.r[2].w[0] == 1, "first dispatch");
    c.pc = base + 4;
    dispatch(c, 0, 0);
    check(c.r[2].w[0] == 2, "cached first snapshot must not shadow the second entry");
    check(!has_code(base + 8), "uncompiled entry should remain missing");
    std::memset(g_ram + base + 4, 0, 4);
    check(!has_code(base + 4), "rewritten instruction must invalidate cached code");
    std::puts("PASS: overlapping entries, cached dispatch, missing entry, and invalidation");
}
