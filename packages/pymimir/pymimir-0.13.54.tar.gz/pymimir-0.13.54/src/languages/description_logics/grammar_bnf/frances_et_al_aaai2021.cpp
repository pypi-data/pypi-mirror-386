/*
 * Copyright (C) 2023 Dominik Drexler and Simon Stahlberg
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 */

#include "frances_et_al_aaai2021.hpp"

#include "mimir/formalism/domain.hpp"
#include "mimir/formalism/predicate.hpp"
#include "mimir/languages/description_logics/constructor_keywords.hpp"
#include "mimir/languages/description_logics/tags.hpp"

#include <fmt/core.h>
#include <fmt/ranges.h>

using namespace mimir::formalism;

namespace mimir::languages::dl::cnf_grammar
{

static void add_concept_intersection(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::concept_intersection);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} <concept> <concept>", dl::keywords::concept_intersection);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_concept_negation(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::concept_negation);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} <concept>", dl::keywords::concept_negation);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_concept_existential_quantification(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::concept_existential_quantification);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} <role> <concept>", dl::keywords::concept_existential_quantification);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_concept_value_restriction(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::concept_value_restriction);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} <role> <concept>", dl::keywords::concept_value_restriction);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_concept_role_value_map_equality(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::concept_intersection);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} <role> <role>", dl::keywords::concept_role_value_map_equality);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_concept_bot(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::concept_bot);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{}", dl::keywords::concept_bot);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_concept_top(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::concept_top);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{}", dl::keywords::concept_top);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_concept_nominal(Object constant, std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}_{}>", dl::keywords::concept_nominal, constant->get_name());
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} \"{}\"", dl::keywords::concept_nominal, constant->get_name());

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_role_transitive_closure(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::role_transitive_closure);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} <role_primitive>", dl::keywords::role_transitive_closure);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_role_inverse(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::role_inverse);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} <role_primitive>", dl::keywords::role_inverse);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_atomic_state(const std::string& keyword, const std::string& predicate_name, std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}_{}>", keyword, predicate_name);

    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} \"{}\"", keyword, predicate_name);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_atomic_goal(const std::string& keyword, const std::string& predicate_name, std::stringstream& out, std::vector<std::string>& head_names)
{
    for (const auto& polarity : { "true", "false" })
    {
        auto head_name = fmt::format("<{}_{}_{}>", keyword, polarity, predicate_name);
        head_names.push_back(head_name);

        auto body_name = fmt::format("@{} \"{}\" {}", keyword, predicate_name, polarity);

        out << fmt::format("    {} ::= {}\n", head_name, body_name);
    }
}

template<IsConceptOrRoleTag D>
static void add_boolean_nonempy(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::boolean_nonempty);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} <{}>", dl::keywords::boolean_nonempty, D::name);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

template<IsConceptOrRoleTag D>
static void add_numeric_count(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::numerical_count);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} <{}>", dl::keywords::numerical_count, D::name);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

static void add_numeric_distance(std::stringstream& out, std::vector<std::string>& head_names)
{
    auto head_name = fmt::format("<{}>", dl::keywords::numerical_distance);
    head_names.push_back(head_name);

    auto body_name = fmt::format("@{} <concept> @role_restriction <role_primitive> <concept_primitive> <concept>", dl::keywords::numerical_distance);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);

    body_name = fmt::format("@{} <concept> <role_primitive> <concept>", dl::keywords::numerical_distance);

    out << fmt::format("    {} ::= {}\n", head_name, body_name);
}

std::string create_frances_et_al_aaai2021_bnf(Domain domain)
{
    // Collect head names to build choice rules.
    auto primitive_head_names = HanaContainer<std::vector<std::string>, ConceptTag, RoleTag, BooleanTag, NumericalTag> {};
    auto head_names = HanaContainer<std::vector<std::string>, ConceptTag, RoleTag, BooleanTag, NumericalTag> {};

    // Builder rules in a stringstream separate from start symbols.
    auto rule_ss = std::stringstream {};
    rule_ss << "[grammar_rules]" << "\n";

    /**
     * Primitives concepts and roles.
     */

    auto& primitive_concept_head_names = boost::hana::at_key(head_names, boost::hana::type<ConceptTag> {});

    add_concept_bot(rule_ss, primitive_concept_head_names);

    add_concept_top(rule_ss, primitive_concept_head_names);

    for (const auto& constant : domain->get_constants())
        add_concept_nominal(constant, rule_ss, primitive_concept_head_names);

    boost::hana::for_each(domain->get_hana_predicates(),
                          [&](auto&& pair)
                          {
                              const auto& predicates = boost::hana::second(pair);

                              for (const auto& predicate : predicates)
                              {
                                  if (predicate->get_arity() == 0)
                                  {
                                      auto& boolean_head_names = boost::hana::at_key(primitive_head_names, boost::hana::type<BooleanTag> {});

                                      add_atomic_state(dl::keywords::boolean_atomic_state, predicate->get_name(), rule_ss, boolean_head_names);
                                  }
                                  else if (predicate->get_arity() == 1)
                                  {
                                      auto& concept_head_names = boost::hana::at_key(primitive_head_names, boost::hana::type<ConceptTag> {});

                                      add_atomic_state(dl::keywords::concept_atomic_state, predicate->get_name(), rule_ss, concept_head_names);

                                      add_atomic_goal(dl::keywords::concept_atomic_goal, predicate->get_name(), rule_ss, concept_head_names);
                                  }
                                  else if (predicate->get_arity() == 2)
                                  {
                                      auto& role_head_names = boost::hana::at_key(primitive_head_names, boost::hana::type<RoleTag> {});

                                      add_atomic_state(dl::keywords::role_atomic_state, predicate->get_name(), rule_ss, role_head_names);

                                      add_atomic_goal(dl::keywords::role_atomic_goal, predicate->get_name(), rule_ss, role_head_names);
                                  }
                              }
                          });

    // Create a rune alternative for primitives.
    boost::hana::for_each(primitive_head_names,
                          [&](auto&& pair)
                          {
                              const auto& key = boost::hana::first(pair);
                              const auto& second = boost::hana::second(pair);
                              using KeyType = typename decltype(+key)::type;

                              // Construct the primitive head name
                              std::string primitives_head_name = fmt::format("<{}_primitive>", KeyType::name);

                              // Add it to head_names
                              boost::hana::at_key(head_names, key).push_back(primitives_head_name);

                              // Format rule with alternatives using fmt::join
                              rule_ss << fmt::format("    {} ::= {}\n", primitives_head_name, fmt::join(second, " | "));
                          });

    /**
     * Composites
     */

    auto& concept_head_names = boost::hana::at_key(head_names, boost::hana::type<ConceptTag> {});
    auto& role_head_names = boost::hana::at_key(head_names, boost::hana::type<RoleTag> {});

    /* Concepts */

    add_concept_intersection(rule_ss, concept_head_names);

    add_concept_negation(rule_ss, concept_head_names);

    add_concept_existential_quantification(rule_ss, concept_head_names);

    add_concept_value_restriction(rule_ss, concept_head_names);

    add_concept_role_value_map_equality(rule_ss, concept_head_names);

    /* Roles */

    add_role_transitive_closure(rule_ss, role_head_names);

    add_role_inverse(rule_ss, role_head_names);

    /* Booleans */
    auto& boolean_head_names = boost::hana::at_key(head_names, boost::hana::type<BooleanTag> {});

    add_boolean_nonempy<ConceptTag>(rule_ss, boolean_head_names);

    add_boolean_nonempy<RoleTag>(rule_ss, boolean_head_names);

    /* Numerical */
    auto& numerical_head_names = boost::hana::at_key(head_names, boost::hana::type<NumericalTag> {});

    add_numeric_count<ConceptTag>(rule_ss, numerical_head_names);

    add_numeric_count<RoleTag>(rule_ss, numerical_head_names);

    add_numeric_distance(rule_ss, numerical_head_names);

    auto start_ss = std::stringstream {};
    start_ss << "[start_symbols]" << "\n";

    boost::hana::for_each(head_names,
                          [&](auto&& pair)
                          {
                              const auto& key = boost::hana::first(pair);
                              const auto& second = boost::hana::second(pair);
                              using KeyType = typename decltype(+key)::type;

                              // Format start symbol
                              start_ss << fmt::format("    {} ::= <{}_start>\n", KeyType::name, KeyType::name);

                              // Format start rule
                              rule_ss << fmt::format("    <{}_start> ::= <{}>\n", KeyType::name, KeyType::name);

                              // Join elements using fmt::join
                              std::string alternatives = fmt::format("{}", fmt::join(second, " | "));

                              // Add primitive alternative
                              alternatives = fmt::format("{} | <{}_primitive>", alternatives, KeyType::name);

                              rule_ss << fmt::format("    <{}> ::= {}\n", KeyType::name, alternatives);
                          });

    auto ss = std::stringstream {};
    ss << start_ss.str();
    ss << rule_ss.str();

    return ss.str();
}

}
