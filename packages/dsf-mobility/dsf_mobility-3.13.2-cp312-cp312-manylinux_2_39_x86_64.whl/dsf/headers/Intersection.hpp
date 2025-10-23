/// @file src/dsf/headers/Intersection.hpp
/// @brief Header file for the Intersection class

/// @details This file contains the definition of the Intersection class. The Intersection class
///          represents a node in the road network. It is derived from the Node class and has a
///          multimap of agents waiting to pass through the intersection. Agents are ordered by
///          their angle difference, emulating real-world precedence.

#pragma once

#include "Agent.hpp"
#include "RoadJunction.hpp"

#include <format>
#include <map>
#include <memory>
#include <set>

namespace dsf {
  /// @brief The Intersection class represents a node in the network.
  /// @tparam Id The type of the node's id. It must be an unsigned integral type.
  class Intersection : public RoadJunction {
  protected:
    std::multimap<int16_t, std::unique_ptr<Agent>> m_agents;
    std::set<Id>
        m_streetPriorities;  // A set containing the street ids that have priority - like main roads
    Size m_agentCounter;

  public:
    /// @brief Construct a new Intersection object
    /// @param id The node's id
    explicit Intersection(Id id) : RoadJunction{id} {};
    /// @brief Construct a new Intersection object
    /// @param id The node's id
    /// @param coords A std::pair containing the node's coordinates
    Intersection(Id id, std::pair<double, double> coords) : RoadJunction{id, coords} {};

    Intersection(RoadJunction const& node) : RoadJunction{node} {};

    Intersection(Intersection const&) = delete;

    virtual ~Intersection() = default;

    /// @brief Set the node's capacity
    /// @param capacity The node's capacity
    /// @throws std::runtime_error if the capacity is smaller than the current queue size
    void setCapacity(Size capacity) override;

    /// @brief Put an agent in the node
    /// @param agent A std::pair containing the agent's angle difference and id
    /// @details The agent's angle difference is used to order the agents in the node.
    ///          The agent with the smallest angle difference is the first one to be
    ///          removed from the node.
    /// @throws std::runtime_error if the node is full
    void addAgent(double angle, std::unique_ptr<Agent> pAgent);
    /// @brief Put an agent in the node
    /// @param agentId The agent's id
    /// @details The agent's angle difference is used to order the agents in the node.
    ///          The agent with the smallest angle difference is the first one to be
    ///          removed from the node.
    /// @throws std::runtime_error if the node is full
    void addAgent(std::unique_ptr<Agent> pAgent);
    // /// @brief Removes an agent from the node
    // /// @param agentId The agent's id
    // void removeAgent(Id agentId);
    /// @brief Set the node streets with priority
    /// @param streetPriorities A std::set containing the node's street priorities
    void setStreetPriorities(std::set<Id> streetPriorities) {
      m_streetPriorities = std::move(streetPriorities);
    }
    /// @brief Add a street to the node street priorities
    /// @param streetId The street's id
    void addStreetPriority(Id streetId) {
      auto const& it{std::find(m_ingoingEdges.cbegin(), m_ingoingEdges.cend(), streetId)};
      if (it == m_ingoingEdges.cend()) {
        throw std::invalid_argument(std::format(
            "Street with id {} is not ingoing edge of intersection with id {}.",
            streetId,
            m_id));
      }
      m_streetPriorities.emplace(streetId);
    }
    /// @brief Returns the node's density
    /// @return double The node's density
    double density() const override {
      return static_cast<double>(m_agents.size()) / this->capacity();
    }
    /// @brief Returns true if the node is full
    /// @return bool True if the node is full
    bool isFull() const override { return m_agents.size() == this->capacity(); }

    /// @brief Get the node's street priorities
    /// @details This function returns a std::set containing the node's street priorities.
    ///        If a street has priority, it means that the agents that are on that street
    ///        have priority over the agents that are on the other streets.
    /// @return std::set<Id> A std::set containing the node's street priorities
    virtual const std::set<Id>& streetPriorities() const { return m_streetPriorities; };
    /// @brief Get the node's agent ids
    /// @return std::set<Id> A std::set containing the node's agent ids
    std::multimap<int16_t, std::unique_ptr<Agent>>& agents() { return m_agents; };
    /// @brief Returns the number of agents that have passed through the node
    /// @return Size The number of agents that have passed through the node
    /// @details This function returns the number of agents that have passed through the node
    ///          since the last time this function was called. It also resets the counter.
    Size agentCounter();

    Size nAgents() const { return m_agents.size(); }

    bool isIntersection() const noexcept final { return true; }
  };
}  // namespace dsf

template <>
struct std::formatter<dsf::Intersection> {
  constexpr auto parse(format_parse_context& ctx) { return ctx.begin(); }

  template <typename FormatContext>
  auto format(dsf::Intersection const& intersection, FormatContext&& ctx) {
    return std::format_to(
        ctx.out(),
        "Intersection(id: {}, name: {}, capacity: {}, transportCapacity: {}, "
        "nAgents: {}, coords: {})",
        intersection.id(),
        intersection.name(),
        intersection.capacity(),
        intersection.transportCapacity(),
        intersection.nAgents(),
        intersection.coords().has_value()
            ? std::format(
                  "({}, {})", intersection.coords()->first, intersection.coords()->second)
            : "N/A");
  }
};