#pragma once

// C/C++
#include <set>

// torch
#include <torch/torch.h>

// kintera
#include <kintera/kintera_formatter.hpp>
#include <kintera/reaction.hpp>
#include <kintera/utils/user_funcs.hpp>

// arg
#include <kintera/add_arg.h>

namespace YAML {
class Node;
}

namespace kintera {

struct NucleationOptions {
  static NucleationOptions from_yaml(const YAML::Node& node);
  NucleationOptions() = default;
  void report(std::ostream& os) const {
    os << "* reactions = " << fmt::format("{}", reactions()) << "\n"
       << "* minT = " << fmt::format("{}", minT()) << " K\n"
       << "* maxT = " << fmt::format("{}", maxT()) << " K\n"
       << "* logsvp = " << fmt::format("{}", logsvp()) << "\n";
  }

  ADD_ARG(std::vector<Reaction>, reactions) = {};
  ADD_ARG(std::vector<double>, minT) = {};
  ADD_ARG(std::vector<double>, maxT) = {};
  ADD_ARG(std::vector<std::string>, logsvp) = {};
};

void add_to_vapor_cloud(std::set<std::string>& vapor_set,
                        std::set<std::string>& cloud_set, NucleationOptions op);

}  // namespace kintera

#undef ADD_ARG
