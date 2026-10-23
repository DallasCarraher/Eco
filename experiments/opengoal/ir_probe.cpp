// Original Eco diagnostic; links to the user's local OpenGOAL compiler.
// IR text may contain recovered game code. Keep its output private.
#include <fstream>
#include <iostream>
#include <sstream>

#include "common/log/log.h"
#include "common/util/FileUtil.h"
#include "goalc/compiler/Compiler.h"
#include "goalc/compiler/IR.h"
#include "third-party/json.hpp"

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: ir-probe OPEN_GOAL_ROOT INPUT.gc OUTPUT.json\n";
    return 2;
  }
  try {
    lg::set_stdout_level(lg::level::warn);
    lg::initialize();
    if (!file_util::setup_project_path(fs::path(argv[1]), true)) return 2;
    Compiler compiler(GameVersion::Jak1, emitter::InstructionSet::ARM64,
                      std::nullopt, "#f", std::make_unique<REPL::Wrapper>(GameVersion::Jak1));
    std::ifstream input(argv[2]);
    if (!input) throw std::runtime_error("cannot read input");
    std::stringstream source;
    source << input.rdbuf();
    auto forms = compiler.get_goos().reader.read_from_string(source.str(), true);
    auto* object = compiler.compile_object_file("eco-feasibility", forms, true);
    nlohmann::json result;
    result["stage"] = "upstream_frontend_ir_before_register_allocation";
    result["cpp_emitted"] = false;
    result["functions"] = nlohmann::json::array();
    for (const auto& function : object->functions()) {
      nlohmann::json item;
      item["name"] = function->name();
      item["instructions"] = nlohmann::json::array();
      for (const auto& instruction : function->code()) {
        item["instructions"].push_back({{"text", instruction->print()},
                                        {"assembly_family", dynamic_cast<IR_Asm*>(instruction.get()) != nullptr}});
      }
      result["functions"].push_back(std::move(item));
    }
    std::ofstream output(argv[3]);
    output << result.dump(2) << '\n';
    if (!output) throw std::runtime_error("cannot write output");
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
