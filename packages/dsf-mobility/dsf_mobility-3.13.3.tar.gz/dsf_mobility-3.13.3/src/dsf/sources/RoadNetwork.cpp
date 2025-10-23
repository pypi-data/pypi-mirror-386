#include "../headers/RoadNetwork.hpp"

#include <algorithm>
#include <ranges>

#include <rapidcsv.h>
#include <simdjson.h>

namespace dsf {
  void RoadNetwork::m_updateMaxAgentCapacity() {
    m_capacity = 0;
    for (auto const& [_, pStreet] : this->edges()) {
      m_capacity += pStreet->capacity();
    }
  }

  void RoadNetwork::m_csvEdgesImporter(std::ifstream& file, const char separator) {
    rapidcsv::Document csvReader(
        file, rapidcsv::LabelParams(0, -1), rapidcsv::SeparatorParams(separator));
    auto const& colNames = csvReader.GetColumnNames();
    bool const bHasGeometry =
        (std::find(colNames.begin(), colNames.end(), "geometry") != colNames.end());
    if (!bHasGeometry) {
      spdlog::warn(
          "No geometry column found in the CSV file. Streets will be imported without "
          "geometry.");
    }
    bool const bHasLanes =
        (std::find(colNames.begin(), colNames.end(), "nlanes") != colNames.end());
    bool const bHasCoilcode =
        (std::find(colNames.begin(), colNames.end(), "coilcode") != colNames.end());
    bool const bHasCustomWeight =
        (std::find(colNames.begin(), colNames.end(), "customWeight") != colNames.end());
    // bool const bHasForbiddenTurns = (std::find(colNames.begin(), colNames.end(), "forbiddenTurns") != colNames.end());

    auto const rowCount = csvReader.GetRowCount();
    for (std::size_t i = 0; i < rowCount; ++i) {
      auto const sourceId = csvReader.GetCell<Id>("source", i);
      auto const targetId = csvReader.GetCell<Id>("target", i);
      if (sourceId == targetId) {
        spdlog::warn("Skipping self-loop edge {}->{}", sourceId, targetId);
        continue;
      }
      auto const streetId = csvReader.GetCell<Id>("id", i);
      auto const dLength = csvReader.GetCell<double>("length", i);
      auto const name = csvReader.GetCell<std::string>("name", i);
      std::vector<std::pair<double, double>> coords;
      if (bHasGeometry) {
        auto const geometry = csvReader.GetCell<std::string>("geometry", i);
        if (!geometry.empty()) {
          // Geometry is LINESTRING(lon,lat lon,lat ...)
          std::istringstream geom{geometry};
          std::string pair;
          std::getline(geom, pair, '(');
          while (std::getline(geom, pair, ',')) {
            pair.erase(pair.begin(),
                       std::find_if(pair.begin(), pair.end(), [](unsigned char ch) {
                         return !std::isspace(ch);
                       }));

            // Trim trailing spaces
            pair.erase(std::find_if(pair.rbegin(),
                                    pair.rend(),
                                    [](unsigned char ch) { return !std::isspace(ch); })
                           .base(),
                       pair.end());
            // Create a stream for each coordinate pair to split by comma
            std::istringstream pairStream(pair);
            std::string lon, lat;
            std::getline(pairStream, lon, ' ');
            std::getline(pairStream, lat);  // read the rest for latitude
            // Remove ')' from lat if present
            if (lat.back() == ')') {
              lat.pop_back();
            }
            auto dLon{0.}, dLat{0.};
            try {
              dLon = std::stod(lon);
              dLat = std::stod(lat);
            } catch (const std::invalid_argument& e) {
              spdlog::error("Invalid coordinates ({}, {}) for edge {}->{}",
                            lon,
                            lat,
                            sourceId,
                            targetId);
            }
            // Note: The original code stored as (lat, lon) based on your comment.
            coords.emplace_back(dLon, dLat);
          }
        } else {
          coords.emplace_back(node(sourceId)->coords().value());
          coords.emplace_back(node(targetId)->coords().value());
        }
      }

      auto iLanes = 1;
      if (bHasLanes) {
        try {
          iLanes = csvReader.GetCell<int>("nlanes", i);
        } catch (...) {
          spdlog::warn("Invalid number of lanes for edge {}->{}. Defaulting to 1 lane.",
                       sourceId,
                       targetId);
          iLanes = 1;
        }
      }

      double dMaxSpeed = 30.;  // Default to 30 km/h
      try {
        dMaxSpeed = csvReader.GetCell<double>("maxspeed", i);
      } catch (...) {
        spdlog::warn("Invalid maxspeed provided for edge {}->{}. Defaulting to 30 km/h.",
                     sourceId,
                     targetId);
      }
      dMaxSpeed /= 3.6;  // Convert to m/s

      addStreet(Street(streetId,
                       std::make_pair(sourceId, targetId),
                       dLength,
                       dMaxSpeed,
                       iLanes,
                       name,
                       coords));

      if (bHasCoilcode) {
        auto strCoilCode = csvReader.GetCell<std::string>("coilcode", i);
        // Make this lowercase
        std::transform(strCoilCode.begin(),
                       strCoilCode.end(),
                       strCoilCode.begin(),
                       [](unsigned char c) { return std::tolower(c); });
        // Do not warn if the coilcode contains null or nan
        if (!strCoilCode.empty() && strCoilCode != "null" && strCoilCode != "nan") {
          try {
            auto const coilCode{static_cast<Id>(std::stoul(strCoilCode))};
            makeSpireStreet(streetId);
            auto& coil = edge<SpireStreet>(streetId);
            coil.setCode(coilCode);
          } catch (...) {
            spdlog::warn("Invalid coil code for {}", *edge(streetId));
          }
        }
      }
      if (bHasCustomWeight) {
        try {
          edge(streetId)->setWeight(csvReader.GetCell<double>("customWeight", i));
        } catch (...) {
          spdlog::warn("Invalid custom weight for {}", *edge(streetId));
        }
      }
    }
    this->m_nodes.rehash(0);
    this->m_edges.rehash(0);
    // Parse forbidden turns
    // for (auto const& [streetId, forbiddenTurns] : mapForbiddenTurns) {
    //   auto const& pStreet{edge(streetId)};
    //   std::istringstream iss{forbiddenTurns};
    //   std::string pair;
    //   while (std::getline(iss, pair, ',')) {
    //     // Decompose pair = sourceId-targetId
    //     std::istringstream pairStream(pair);
    //     std::string strSourceId, strTargetId;
    //     std::getline(pairStream, strSourceId, '-');
    //     // targetId is the remaining part
    //     std::getline(pairStream, strTargetId);

    //     Id const sourceId{std::stoul(strSourceId)};
    //     Id const targetId{std::stoul(strTargetId)};

    //     pStreet->addForbiddenTurn(edge(sourceId, targetId)->id());
    //   }
    // }
  }
  void RoadNetwork::m_csvNodePropertiesImporter(std::ifstream& file,
                                                const char separator) {
    rapidcsv::Document csvReader(
        file, rapidcsv::LabelParams(0, -1), rapidcsv::SeparatorParams(separator));
    auto const rowCount = csvReader.GetRowCount();
    for (std::size_t i = 0; i < rowCount; ++i) {
      auto const nodeId = csvReader.GetCell<Id>("id", i);
      if (m_nodes.find(nodeId) == m_nodes.end()) {
        spdlog::warn("Node {} not found in the network. Skipping properties import.",
                     nodeId);
        continue;
      }
      auto strType = csvReader.GetCell<std::string>("type", i);
      std::transform(
          strType.begin(), strType.end(), strType.begin(), [](unsigned char c) {
            return std::tolower(c);
          });
      if (strType.find("traffic_signals") != std::string::npos) {
        makeTrafficLight(nodeId, 120);
      } else if (strType.find("roundabout") != std::string::npos) {
        makeRoundabout(nodeId);
      }

      std::pair<double, double> coords;
      auto const& strGeometry = csvReader.GetCell<std::string>("geometry", i);
      if (!strGeometry.empty()) {
        // Geometry is POINT (lon lat)
        std::istringstream geom{strGeometry};
        std::string pair;
        std::getline(geom, pair, '(');
        while (std::getline(geom, pair, ',')) {
          pair.erase(pair.begin(),
                     std::find_if(pair.begin(), pair.end(), [](unsigned char ch) {
                       return !std::isspace(ch);
                     }));

          // Trim trailing spaces
          pair.erase(std::find_if(pair.rbegin(),
                                  pair.rend(),
                                  [](unsigned char ch) { return !std::isspace(ch); })
                         .base(),
                     pair.end());
          // Create a stream for each coordinate pair to split by comma
          std::istringstream pairStream(pair);
          std::string lon, lat;
          std::getline(pairStream, lon, ' ');
          std::getline(pairStream, lat);  // read the rest for latitude
          // Remove ')' from lat if present
          if (lat.back() == ')') {
            lat.pop_back();
          }
          auto dLon{0.}, dLat{0.};
          try {
            dLon = std::stod(lon);
            dLat = std::stod(lat);
          } catch (const std::invalid_argument& e) {
            spdlog::error("Invalid coordinates ({}, {}) for node {}", lon, lat, nodeId);
          }
          // Note: The original code stored as (lat, lon) based on your comment.
          coords = std::make_pair(dLon, dLat);
        }
        auto const& pNode{node(nodeId)};
        // Assign coords or check if these coords match the existing ones
        if (!pNode->coords().has_value()) {
          pNode->setCoords(coords);
        } else {
          auto const& [oldLon, oldLat] = pNode->coords().value();
          auto const& [newLon, newLat] = coords;
          if (std::abs(oldLat - newLat) > std::numeric_limits<double>::epsilon() ||
              std::abs(oldLon - newLon) > std::numeric_limits<double>::epsilon()) {
            spdlog::error(
                "Node {} coordinates from properties file ({}, {}) do not match existing "
                "coordinates ({}, {}). Keeping existing coordinates.",
                nodeId,
                newLat,
                newLon,
                oldLat,
                oldLon);
          }
        }
      }
    }
  }
  void RoadNetwork::m_jsonEdgesImporter(std::ifstream& file, const bool bCreateInverse) {
    // Read the file into a string
    std::string json_str((std::istreambuf_iterator<char>(file)),
                         std::istreambuf_iterator<char>());
    simdjson::dom::parser parser;
    simdjson::dom::element root;
    auto error = parser.parse(json_str).get(root);
    if (error) {
      throw std::runtime_error("Failed to parse JSON: " +
                               std::string(simdjson::error_message(error)));
    }

    for (auto feature : root["features"]) {
      auto edge_properties = feature["properties"];

      auto const& src_node_id = static_cast<Id>(edge_properties["source"].get_uint64());
      auto const& dst_node_id = static_cast<Id>(edge_properties["target"].get_uint64());
      if (src_node_id == dst_node_id) {
        spdlog::warn("Skipping self-loop edge {}->{}", src_node_id, dst_node_id);
        continue;
      }

      std::vector<std::pair<double, double>> geometry;
      for (auto const& coord : feature["geometry"]["coordinates"]) {
        auto const& lat = coord.at(1);
        auto const& lon = coord.at(0);
        geometry.emplace_back(lat, lon);
      }
      auto const& edge_id = static_cast<Id>(edge_properties["id"].get_uint64());
      auto const& edge_length =
          static_cast<double>(edge_properties["length"].get_double());

      // Robust extraction for maxspeed
      double edge_maxspeed = 30.0;
      if (!edge_properties["maxspeed"].is_null()) {
        auto maxspeed_val = edge_properties["maxspeed"];
        if (maxspeed_val.is_string()) {
          try {
            edge_maxspeed = std::stod(std::string(maxspeed_val.get_string().value()));
          } catch (...) {
            edge_maxspeed = 30.0;
          }
        } else if (maxspeed_val.is_number()) {
          edge_maxspeed = maxspeed_val.get_double();
        }
      }
      edge_maxspeed /= 3.6;

      // Robust extraction for lanes
      auto edge_lanes{1u};
      if (!edge_properties["nlanes"].is_null()) {
        auto lanes_val = edge_properties["nlanes"];
        if (lanes_val.is_number()) {
          edge_lanes = lanes_val.get_uint64();
        } else if (lanes_val.is_string()) {
          try {
            edge_lanes = std::stoul(std::string(lanes_val.get_string().value()));
          } catch (...) {
            edge_lanes = 1;
          }
        }
      }

      // Robust extraction for name
      std::string name = "";
      if (!edge_properties["name"].is_null() && edge_properties["name"].is_string()) {
        name = std::string(edge_properties["name"].get_string().value());
      }

      if (!bCreateInverse) {
        addStreet(Street(edge_id,
                         std::make_pair(src_node_id, dst_node_id),
                         edge_length,
                         edge_maxspeed,
                         edge_lanes,
                         name,
                         geometry));
        // Check if there is coilcode property
        if (!edge_properties["coilcode"].is_null() &&
            edge_properties["coilcode"].is_uint64()) {
          makeSpireStreet(edge_id);
          auto& coil = edge<SpireStreet>(edge_id);
          try {
            coil.setCode(edge_properties["coilcode"].get_uint64());
          } catch (...) {
            spdlog::warn("Invalid coil code ({}) for {}",
                         edge_properties["coilcode"].get_string().value(),
                         *edge(edge_id));
          }
        }
      } else {
        addStreet(Street(edge_id * 10,
                         std::make_pair(src_node_id, dst_node_id),
                         edge_length,
                         edge_maxspeed,
                         edge_lanes,
                         name,
                         geometry));
        addStreet(Street(
            edge_id * 10 + 1,
            std::make_pair(dst_node_id, src_node_id),
            edge_length,
            edge_maxspeed,
            edge_lanes,
            name,
            std::vector<std::pair<double, double>>(geometry.rbegin(), geometry.rend())));
      }
    }
    this->m_nodes.rehash(0);
    this->m_edges.rehash(0);
  }

  RoadNetwork::RoadNetwork() : Network{AdjacencyMatrix()}, m_capacity{0} {}

  RoadNetwork::RoadNetwork(AdjacencyMatrix const& adj) : Network{adj}, m_capacity{0} {}

  Size RoadNetwork::nCoils() const {
    return std::count_if(m_edges.cbegin(), m_edges.cend(), [](auto const& pair) {
      return pair.second->isSpire();
    });
  }

  Size RoadNetwork::nIntersections() const {
    return std::count_if(m_nodes.cbegin(), m_nodes.cend(), [](auto const& pair) {
      return pair.second->isIntersection();
    });
  }
  Size RoadNetwork::nRoundabouts() const {
    return std::count_if(m_nodes.cbegin(), m_nodes.cend(), [](auto const& pair) {
      return pair.second->isRoundabout();
    });
  }
  Size RoadNetwork::nTrafficLights() const {
    return std::count_if(m_nodes.cbegin(), m_nodes.cend(), [](auto const& pair) {
      return pair.second->isTrafficLight();
    });
  }

  void RoadNetwork::initTrafficLights(Delay const minGreenTime) {
    for (auto& [_, pNode] : m_nodes) {
      if (!pNode->isTrafficLight()) {
        continue;
      }
      auto& tl = static_cast<TrafficLight&>(*pNode);
      if (!tl.streetPriorities().empty() || !tl.cycles().empty()) {
        continue;
      }
      auto const& inNeighbours = pNode->ingoingEdges();
      std::map<Id, int, std::greater<int>> capacities;
      std::unordered_map<Id, double> streetAngles;
      std::unordered_map<Id, double> maxSpeeds;
      std::unordered_map<Id, int> nLanes;
      std::unordered_map<Id, std::string> streetNames;
      double higherSpeed{0.}, lowerSpeed{std::numeric_limits<double>::max()};
      int higherNLanes{0}, lowerNLanes{std::numeric_limits<int>::max()};
      if (inNeighbours.size() < 3) {
        spdlog::warn("Not enough in neighbours {} for Traffic Light {}",
                     inNeighbours.size(),
                     pNode->id());
        // Replace with a normal intersection
        auto const& coordinates{pNode->coords()};
        if (coordinates.has_value()) {
          pNode = std::make_unique<Intersection>(pNode->id(), *coordinates);
        } else {
          pNode = std::make_unique<Intersection>(pNode->id());
        }
        continue;
      }
      for (auto const& edgeId : inNeighbours) {
        auto const& pStreet{edge(edgeId)};

        double const speed{pStreet->maxSpeed()};
        int const nLan{pStreet->nLanes()};
        auto const cap{pStreet->capacity()};
        capacities.emplace(pStreet->id(), cap);
        auto angle{pStreet->angle()};
        if (angle < 0.) {
          angle += 2 * std::numbers::pi;
        }
        streetAngles.emplace(pStreet->id(), angle);

        maxSpeeds.emplace(pStreet->id(), speed);
        nLanes.emplace(pStreet->id(), nLan);
        streetNames.emplace(pStreet->id(), pStreet->name());

        higherSpeed = std::max(higherSpeed, speed);
        lowerSpeed = std::min(lowerSpeed, speed);

        higherNLanes = std::max(higherNLanes, nLan);
        lowerNLanes = std::min(lowerNLanes, nLan);
      }
      {
        std::vector<std::pair<Id, double>> sortedAngles;
        std::copy(
            streetAngles.begin(), streetAngles.end(), std::back_inserter(sortedAngles));
        std::sort(sortedAngles.begin(),
                  sortedAngles.end(),
                  [](auto const& a, auto const& b) { return a.second < b.second; });
        streetAngles.clear();
        for (auto const& [streetId, angle] : sortedAngles) {
          streetAngles.emplace(streetId, angle);
        }
      }
      if (tl.streetPriorities().empty()) {
        /*************************************************************
         * 1. Check for street names with multiple occurrences
         * ***********************************************************/
        std::unordered_map<std::string, int> counts;
        for (auto const& [streetId, name] : streetNames) {
          if (name.empty()) {
            // Ignore empty names
            continue;
          }
          if (!counts.contains(name)) {
            counts[name] = 1;
          } else {
            ++counts.at(name);
          }
        }
        // Check if spdlog is in debug mode
        if (spdlog::get_level() <= spdlog::level::debug) {
          for (auto const& [name, count] : counts) {
            spdlog::debug("Street name {} has {} occurrences", name, count);
          }
        }
        for (auto const& [streetId, name] : streetNames) {
          if (!name.empty() && counts.at(name) > 1) {
            tl.addStreetPriority(streetId);
          }
        }
      }
      if (tl.streetPriorities().empty() && higherSpeed != lowerSpeed) {
        /*************************************************************
         * 2. Check for street names with same max speed
         * ***********************************************************/
        for (auto const& [sid, speed] : maxSpeeds) {
          if (speed == higherSpeed) {
            tl.addStreetPriority(sid);
          }
        }
      }
      if (tl.streetPriorities().empty() && higherNLanes != lowerNLanes) {
        /*************************************************************
         * 2. Check for street names with same number of lanes
         * ***********************************************************/
        for (auto const& [sid, nLan] : nLanes) {
          if (nLan == higherNLanes) {
            tl.addStreetPriority(sid);
          }
        }
      }
      if (tl.streetPriorities().empty()) {
        /*************************************************************
         * 3. Check for streets with opposite angles
         * ***********************************************************/
        auto const& streetId = streetAngles.begin()->first;
        auto const& angle = streetAngles.begin()->second;
        for (auto const& [streetId2, angle2] : streetAngles) {
          if (std::abs(angle - angle2) > 0.75 * std::numbers::pi) {
            tl.addStreetPriority(streetId);
            tl.addStreetPriority(streetId2);
            break;
          }
        }
      }
      if (tl.streetPriorities().empty()) {
        spdlog::warn("Failed to auto-init Traffic Light {} - going random", pNode->id());
        // Assign first and third keys of capacity map
        auto it = capacities.begin();
        auto const& firstKey = it->first;
        ++it;
        ++it;
        auto const& thirdKey = it->first;
        tl.addStreetPriority(firstKey);
        tl.addStreetPriority(thirdKey);
      }

      // Assign cycles
      std::pair<Delay, Delay> greenTimes;
      {
        auto capPriority{0.}, capNoPriority{0.};
        std::unordered_map<Id, double> normCapacities;
        auto sum{0.};
        for (auto const& [streetId, cap] : capacities) {
          sum += cap;
        }
        for (auto const& [streetId, cap] : capacities) {
          normCapacities.emplace(streetId, cap / sum);
        }
        for (auto const& [streetId, normCap] : normCapacities) {
          if (tl.streetPriorities().contains(streetId)) {
            capPriority += normCap;
          } else {
            capNoPriority += normCap;
          }
        }
        spdlog::debug("Capacities for Traffic Light {}: priority {} no priority {}",
                      pNode->id(),
                      capPriority,
                      capNoPriority);
        greenTimes = std::make_pair(static_cast<Delay>(capPriority * tl.cycleTime()),
                                    static_cast<Delay>(capNoPriority * tl.cycleTime()));
      }
      // if one of green times is less than 20, set it to 20 and refactor the other to have the sum to 120
      if (greenTimes.first < minGreenTime) {
        greenTimes.first = minGreenTime;
        greenTimes.second = tl.cycleTime() - minGreenTime;
      }
      if (greenTimes.second < minGreenTime) {
        greenTimes.second = minGreenTime;
        greenTimes.first = tl.cycleTime() - minGreenTime;
      }
      std::for_each(inNeighbours.begin(), inNeighbours.end(), [&](auto const& edgeId) {
        auto const streetId{this->edge(edgeId)->id()};
        auto const nLane{nLanes.at(streetId)};
        Delay greenTime{greenTimes.first};
        Delay phase{0};
        if (!tl.streetPriorities().contains(streetId)) {
          phase = greenTime;
          greenTime = greenTimes.second;
        }
        spdlog::debug("Setting cycle for street {} with green time {} and phase {}",
                      streetId,
                      greenTime,
                      phase);
        switch (nLane) {
          case 3:
            tl.setCycle(streetId,
                        dsf::Direction::RIGHTANDSTRAIGHT,
                        TrafficLightCycle{static_cast<Delay>(greenTime * 2. / 3), phase});
            tl.setCycle(
                streetId,
                dsf::Direction::LEFT,
                TrafficLightCycle{
                    static_cast<Delay>(greenTime / 3.),
                    static_cast<Delay>(phase + static_cast<Delay>(greenTime * 2. / 3))});
            break;
          default:
            tl.setCycle(
                streetId, dsf::Direction::ANY, TrafficLightCycle{greenTime, phase});
            break;
        }
      });
    }
  }
  void RoadNetwork::autoMapStreetLanes() {
    auto const& nodes = this->nodes();
    std::for_each(nodes.cbegin(), nodes.cend(), [this](auto const& pair) {
      auto const& pNode{pair.second};
      auto const& inNeighbours{pNode->ingoingEdges()};
      auto const& outNeighbours{pNode->outgoingEdges()};
      int maxPriority{0};
      std::for_each(inNeighbours.cbegin(),
                    inNeighbours.cend(),
                    [this, &pNode, &maxPriority](auto const& edgeId) {
                      auto const& pStreet{this->edge(edgeId)};
                      maxPriority = std::max(maxPriority, pStreet->priority());
                    });
      std::for_each(outNeighbours.cbegin(),
                    outNeighbours.cend(),
                    [this, &pNode, &maxPriority](auto const& edgeId) {
                      auto const& pStreet{this->edge(edgeId)};
                      maxPriority = std::max(maxPriority, pStreet->priority());
                    });
      std::for_each(
          inNeighbours.cbegin(),
          inNeighbours.cend(),
          [this, &pNode, &outNeighbours, &maxPriority](auto const& edgeId) {
            auto const& pInStreet{this->edge(edgeId)};
            auto const nLanes{pInStreet->nLanes()};
            if (nLanes == 1) {
              return;
            }
            std::multiset<Direction> allowedTurns;
            std::for_each(
                outNeighbours.cbegin(),
                outNeighbours.cend(),
                [this, &pNode, &pInStreet, &allowedTurns, &maxPriority](
                    auto const& edgeId) {
                  auto const& pOutStreet{this->edge(edgeId)};
                  if (pOutStreet->target() == pInStreet->source() ||
                      pInStreet->forbiddenTurns().contains(pOutStreet->id())) {
                    return;
                  }
                  auto const deltaAngle{pOutStreet->deltaAngle(pInStreet->angle())};
                  auto const& outOppositeStreet{
                      this->street(pOutStreet->target(), pOutStreet->source())};
                  if (!outOppositeStreet) {
                    return;
                  }
                  // Actually going straight means remain on the same road, thus...
                  if (((pInStreet->priority() == maxPriority) ==
                       (outOppositeStreet->get()->priority() == maxPriority)) &&
                      !allowedTurns.contains(Direction::STRAIGHT)) {
                    spdlog::debug("Street {} prioritized STRAIGHT", pInStreet->id());
                    if (allowedTurns.contains(Direction::STRAIGHT) &&
                        !allowedTurns.contains(Direction::RIGHT)) {
                      allowedTurns.emplace(Direction::RIGHT);
                    } else {
                      allowedTurns.emplace(Direction::STRAIGHT);
                    }
                    // if (!allowedTurns.contains(Direction::STRAIGHT)) {
                    // allowedTurns.emplace(Direction::STRAIGHT);
                    // return;
                    // }
                  } else if (std::abs(deltaAngle) < std::numbers::pi) {
                    // Logger::debug(std::format("Angle in {} - angle out {}",
                    //                           pInStreet->angle(),
                    //                           pOutStreet->angle()));
                    // Logger::debug(std::format("Delta: {}", deltaAngle));
                    if (std::abs(deltaAngle) < std::numbers::pi / 8) {
                      spdlog::debug("Street {} -> {} can turn STRAIGHT",
                                    pInStreet->source(),
                                    pInStreet->target());
                      allowedTurns.emplace(Direction::STRAIGHT);
                    } else if (deltaAngle < 0.) {
                      spdlog::debug("Street {} -> {} can turn RIGHT",
                                    pInStreet->source(),
                                    pInStreet->target());
                      allowedTurns.emplace(Direction::RIGHT);
                    } else if (deltaAngle > 0.) {
                      spdlog::debug("Street {} -> {} can turn LEFT",
                                    pInStreet->source(),
                                    pInStreet->target());
                      allowedTurns.emplace(Direction::LEFT);
                    }
                  }
                });
            while (allowedTurns.size() < static_cast<size_t>(nLanes)) {
              if (allowedTurns.contains(Direction::STRAIGHT)) {
                allowedTurns.emplace(Direction::STRAIGHT);
              } else if (allowedTurns.contains(Direction::RIGHT)) {
                allowedTurns.emplace(Direction::RIGHT);
              } else if (allowedTurns.contains(Direction::LEFT)) {
                allowedTurns.emplace(Direction::LEFT);
              } else {
                allowedTurns.emplace(Direction::ANY);
              }
            }
            // If allowedTurns contains all RIGHT, STRAIGHT and LEFT, transform RIGHT into RIGHTANDSTRAIGHT
            if (allowedTurns.size() > static_cast<size_t>(nLanes)) {
              if (pNode->isTrafficLight()) {
                auto& tl = static_cast<TrafficLight&>(*pNode);
                auto const& cycles{tl.cycles()};
                if (cycles.contains(pInStreet->id())) {
                  if (cycles.size() == static_cast<size_t>(nLanes)) {
                    // Replace with the traffic light cycles
                    spdlog::debug("Using traffic light {} cycles for street {} -> {}",
                                  tl.id(),
                                  pInStreet->source(),
                                  pInStreet->target());
                    auto const& cycle{cycles.at(pInStreet->id())};
                    allowedTurns.clear();
                    for (auto const& [direction, cycle] : cycle) {
                      allowedTurns.emplace(direction);
                    }
                  } else if (cycles.at(pInStreet->id())
                                 .contains(Direction::LEFTANDSTRAIGHT)) {
                    allowedTurns.erase(Direction::LEFT);
                    allowedTurns.erase(Direction::STRAIGHT);
                    allowedTurns.emplace(Direction::LEFTANDSTRAIGHT);
                  } else if (cycles.at(pInStreet->id())
                                 .contains(Direction::RIGHTANDSTRAIGHT)) {
                    allowedTurns.erase(Direction::RIGHT);
                    allowedTurns.erase(Direction::STRAIGHT);
                    allowedTurns.emplace(Direction::RIGHTANDSTRAIGHT);
                  }
                }
              }
            }
            if (allowedTurns.size() > static_cast<size_t>(nLanes)) {
              // if one is duplicate, remove it
              std::set<Direction> uniqueDirections;
              std::copy(allowedTurns.begin(),
                        allowedTurns.end(),
                        std::inserter(uniqueDirections, uniqueDirections.begin()));
              allowedTurns.clear();
              std::copy(uniqueDirections.begin(),
                        uniqueDirections.end(),
                        std::inserter(allowedTurns, allowedTurns.begin()));
            }
            while (allowedTurns.size() < static_cast<size_t>(nLanes)) {
              if (allowedTurns.contains(Direction::STRAIGHT)) {
                allowedTurns.emplace(Direction::STRAIGHT);
              } else if (allowedTurns.contains(Direction::RIGHT)) {
                allowedTurns.emplace(Direction::RIGHT);
              } else if (allowedTurns.contains(Direction::LEFT)) {
                allowedTurns.emplace(Direction::LEFT);
              } else {
                allowedTurns.emplace(Direction::ANY);
              }
            }
            switch (nLanes) {
              case 1:
                // Leaving Direction::ANY for one lane streets is the less painful option
                break;
              case 2:
                if (allowedTurns.contains(Direction::STRAIGHT) &&
                    allowedTurns.contains(Direction::RIGHT) &&
                    allowedTurns.contains(Direction::LEFT)) {
                  if (pNode->isTrafficLight()) {
                    auto& tl = static_cast<TrafficLight&>(*pNode);
                    auto const& cycles{tl.cycles()};
                    if (cycles.contains(pInStreet->id())) {
                      auto const& cycle{cycles.at(pInStreet->id())};
                      if (cycle.contains(Direction::LEFTANDSTRAIGHT) &&
                          cycle.contains(Direction::RIGHT)) {
                        allowedTurns.erase(Direction::LEFT);
                        allowedTurns.erase(Direction::STRAIGHT);
                        allowedTurns.emplace(Direction::LEFTANDSTRAIGHT);
                        break;
                      }
                    }
                  }
                  allowedTurns.clear();
                  allowedTurns.emplace(Direction::RIGHTANDSTRAIGHT);
                  allowedTurns.emplace(Direction::LEFT);
                }
                if (allowedTurns.size() > 2) {
                  // Remove duplicates
                  std::set<Direction> uniqueDirections;
                  std::copy(allowedTurns.begin(),
                            allowedTurns.end(),
                            std::inserter(uniqueDirections, uniqueDirections.begin()));
                  allowedTurns.clear();
                  std::copy(uniqueDirections.begin(),
                            uniqueDirections.end(),
                            std::inserter(allowedTurns, allowedTurns.begin()));
                }
                [[fallthrough]];
              default:
                // Logger::info(std::format(
                //     "Street {}->{} with {} lanes and {} allowed turns",
                //     pInStreet->source(),
                //     pInStreet->target(),
                //     nLanes,
                //     allowedTurns.size()));
                assert(allowedTurns.size() == static_cast<size_t>(nLanes));
                // Logger::info(
                //     std::format("Street {}->{} with {} lanes and {} allowed turns",
                //                 pInStreet->source(),
                //                 pInStreet->target(),
                //                 nLanes,
                //                 allowedTurns.size()));
                std::vector<Direction> newMapping(nLanes);
                auto it{allowedTurns.cbegin()};
                for (size_t i{0}; i < allowedTurns.size(); ++i, ++it) {
                  newMapping[i] = *it;
                }
                // If the last one is RIGHTANDSTRAIGHT, move it in front
                if (newMapping.back() == Direction::RIGHTANDSTRAIGHT) {
                  std::rotate(
                      newMapping.rbegin(), newMapping.rbegin() + 1, newMapping.rend());
                }
                pInStreet->setLaneMapping(newMapping);
            }
          });
    });
  }

  void RoadNetwork::adjustNodeCapacities() {
    double value;
    for (auto const& [_, pNode] : nodes()) {
      value = 0.;
      for (auto const& edgeId : pNode->ingoingEdges()) {
        auto const& pStreet{this->edge(edgeId)};
        value += pStreet->nLanes() * pStreet->transportCapacity();
      }
      pNode->setCapacity(value);
      value = 0.;
      for (auto const& edgeId : pNode->outgoingEdges()) {
        auto const& pStreet{this->edge(edgeId)};
        value += pStreet->nLanes() * pStreet->transportCapacity();
      }
      pNode->setTransportCapacity(value == 0. ? 1. : value);
      if (pNode->capacity() == 0) {
        pNode->setCapacity(value);
      }
    }
  }

  void RoadNetwork::importMatrix(const std::string& fileName,
                                 bool isAdj,
                                 double defaultSpeed) {
    // check the file extension
    std::string fileExt = fileName.substr(fileName.find_last_of(".") + 1);
    if (fileExt == "dsf") {
      std::ifstream file{fileName};
      if (!file.is_open()) {
        throw std::runtime_error("Error opening file \"" + fileName + "\" for reading.");
      }
      Size rows, cols;
      file >> rows >> cols;
      if (rows != cols) {
        throw std::invalid_argument("Adjacency matrix must be square");
      }
      Size n{rows};
      addNDefaultNodes<Intersection>(n);
      // each line has 2 elements
      while (!file.eof()) {
        Id index;
        double val;
        file >> index >> val;
        const auto srcId{static_cast<Id>(index / n)};
        const auto dstId{static_cast<Id>(index % n)};
        if (isAdj) {
          addStreet(Street(index, std::make_pair(srcId, dstId)));
        } else {
          addStreet(Street(index, std::make_pair(srcId, dstId), val));
        }
        edge(index)->setMaxSpeed(defaultSpeed);
      }
    } else {
      // default case: read the file as a matrix with the first two elements being the number of rows and columns and
      // the following elements being the matrix elements
      std::ifstream file{fileName};
      if (!file.is_open()) {
        throw std::runtime_error("Error opening file \"" + fileName + "\" for reading.");
      }
      Size rows, cols;
      file >> rows >> cols;
      if (rows != cols) {
        throw std::invalid_argument(
            "Adjacency matrix must be square. Rows: " + std::to_string(rows) +
            " Cols: " + std::to_string(cols));
      }
      Size n{rows};
      addNDefaultNodes<Intersection>(n);
      if (n * n > std::numeric_limits<Id>::max()) {
        throw std::invalid_argument(
            "Matrix size is too large for the current type of Id.");
      }
      Id index{0};
      while (!file.eof()) {
        double value;
        file >> value;
        if (value < 0) {
          throw std::invalid_argument(
              std::format("Element at index {} is negative ({}).", index, value));
        }
        if (value > 0) {
          const auto srcId{static_cast<Id>(index / n)};
          const auto dstId{static_cast<Id>(index % n)};
          if (isAdj) {
            addStreet(Street(index, std::make_pair(srcId, dstId)));
          } else {
            addStreet(Street(index, std::make_pair(srcId, dstId), value));
          }
          edge(index)->setMaxSpeed(defaultSpeed);
        }
        ++index;
      }
    }
    this->m_updateMaxAgentCapacity();
  }

  void RoadNetwork::importCoordinates(const std::string& fileName) {
    std::string fileExt = fileName.substr(fileName.find_last_of(".") + 1);
    if (fileExt == "dsf") {
      // first input number is the number of nodes
      std::ifstream file{fileName};
      if (!file.is_open()) {
        throw std::runtime_error("Error opening file \"" + fileName + "\" for reading.");
      }
      Size n;
      file >> n;
      if (n < this->nNodes()) {
        throw std::invalid_argument("Number of node coordinates in file is too small.");
      }
      double lat, lon;
      for (Size i{0}; i < n; ++i) {
        file >> lon >> lat;
        try {
          node(i)->setCoords(std::make_pair(lon, lat));
        } catch (...) {
          spdlog::warn(std::format("Node with id {} not found.", i));
        }
      }
    } else if (fileExt == "csv") {
      std::ifstream ifs{fileName};
      if (!ifs.is_open()) {
        throw std::runtime_error("Error opening file \"" + fileName + "\" for reading.");
      }
      // Check if the first line is nodeId;lat;lon
      std::string line;
      std::getline(ifs, line);
      if (line != "id;lat;lon;type") {
        throw std::invalid_argument("Invalid file format.");
      }
      double dLat, dLon;
      while (!ifs.eof()) {
        std::getline(ifs, line);
        if (line.empty()) {
          continue;
        }
        std::istringstream iss{line};
        std::string nodeId, lat, lon, type;
        std::getline(iss, nodeId, ';');
        std::getline(iss, lat, ';');
        std::getline(iss, lon, ';');
        std::getline(iss, type, '\n');
        dLon = lon == "Nan" ? 0. : std::stod(lon);
        dLat = lat == "Nan" ? 0. : std::stod(lat);
        auto const& nodes{this->nodes()};
        auto it = nodes.find(std::stoul(nodeId));
        if (it != nodes.cend()) {
          auto const& pNode{it->second};
          pNode->setCoords(std::make_pair(dLat, dLon));
          if (type == "traffic_light" && !pNode->isTrafficLight()) {
            makeTrafficLight(it->first, 60);
          } else if (type == "roundabout" && !pNode->isRoundabout()) {
            makeRoundabout(it->first);
          }
        } else {
          spdlog::warn("Node with id {} not found. Skipping coordinates ({}, {}).",
                       nodeId,
                       dLat,
                       dLon);
        }
      }
    } else {
      throw std::invalid_argument(
          std::format("File extension ({}) not supported", fileExt));
    }
    for (auto const& [_, pEdge] : edges()) {
      auto const& pSourceNode{node(pEdge->source())};
      auto const& pTargetNode{node(pEdge->target())};
      pEdge->setGeometry(std::vector<std::pair<double, double>>{
          *(pSourceNode->coords()), *(pTargetNode->coords())});
    }
  }

  void RoadNetwork::importTrafficLights(const std::string& fileName) {
    std::ifstream file{fileName};
    if (!file.is_open()) {
      throw std::runtime_error("Error opening file \"" + fileName + "\" for reading.");
    }
    std::unordered_map<Id, Delay> storedGreenTimes;
    std::string line;
    std::getline(file, line);  // skip first line
    while (std::getline(file, line)) {
      if (line.empty()) {
        continue;
      }
      std::istringstream iss{line};
      std::string strId, streetSource, strCycleTime, strGT;
      // id;streetSource;cycleTime;greenTime
      std::getline(iss, strId, ';');
      std::getline(iss, streetSource, ';');
      std::getline(iss, strCycleTime, ';');
      std::getline(iss, strGT, '\n');

      auto const cycleTime{static_cast<Delay>(std::stoul(strCycleTime))};
      // Cast node(id) to traffic light
      auto& pNode{node(std::stoul(strId))};
      if (!pNode->isTrafficLight()) {
        pNode = std::make_unique<TrafficLight>(
            pNode->id(), cycleTime, pNode->coords().value());
      }
      auto& tl = static_cast<TrafficLight&>(*pNode);
      auto const streetId{edge(std::stoul(streetSource), pNode->id())->id()};
      auto const greenTime{static_cast<Delay>(std::stoul(strGT))};
      if (!storedGreenTimes.contains(pNode->id())) {
        storedGreenTimes.emplace(pNode->id(), greenTime);
      }
      auto const storedGT{storedGreenTimes.at(pNode->id())};
      if (storedGT == greenTime) {
        auto cycle = TrafficLightCycle(greenTime, 0);
        tl.setCycle(streetId, dsf::Direction::ANY, cycle);
      } else {
        auto cycle = TrafficLightCycle(greenTime, storedGT);
        tl.setCycle(streetId, dsf::Direction::ANY, cycle);
      }
    }
  }

  void RoadNetwork::exportMatrix(std::string path, bool isAdj) {
    std::ofstream file{path};
    if (!file.is_open()) {
      throw std::runtime_error("Error opening file \"" + path + "\" for writing.");
    }
    auto const N{nNodes()};
    file << N << '\t' << N;
    if (isAdj) {
      std::for_each(m_edges.cbegin(), m_edges.cend(), [&N, &file](auto const& pair) {
        file << '\n' << pair.second->source() * N + pair.second->target() << '\t' << 1;
      });
    } else {
      std::for_each(m_edges.cbegin(), m_edges.cend(), [&N, &file](auto const& pair) {
        file << '\n' << pair.second->id() << '\t' << pair.second->length();
      });
    }
  }

  TrafficLight& RoadNetwork::makeTrafficLight(Id const nodeId,
                                              Delay const cycleTime,
                                              Delay const counter) {
    auto& pNode = node(nodeId);
    pNode = std::make_unique<TrafficLight>(*pNode, cycleTime, counter);
    return node<TrafficLight>(nodeId);
  }

  Roundabout& RoadNetwork::makeRoundabout(Id nodeId) {
    auto& pNode = node(nodeId);
    pNode = std::make_unique<Roundabout>(*pNode);
    return node<Roundabout>(nodeId);
  }

  Station& RoadNetwork::makeStation(Id nodeId, const unsigned int managementTime) {
    auto& pNode = node(nodeId);
    pNode = std::make_unique<Station>(*pNode, managementTime);
    return node<Station>(nodeId);
  }
  void RoadNetwork::makeStochasticStreet(Id streetId, double const flowRate) {
    auto& pStreet = edge(streetId);
    pStreet = std::unique_ptr<StochasticStreet>(
        new StochasticStreet(std::move(*pStreet), flowRate));
  }
  void RoadNetwork::makeSpireStreet(Id streetId) {
    auto& pStreet = edge(streetId);
    if (pStreet->isStochastic()) {
      pStreet = std::unique_ptr<StochasticSpireStreet>(new StochasticSpireStreet(
          std::move(*pStreet), dynamic_cast<StochasticStreet&>(*pStreet).flowRate()));
      return;
    }
    pStreet = std::unique_ptr<SpireStreet>(new SpireStreet(std::move(*pStreet)));
  }

  void RoadNetwork::addStreet(Street&& street) {
    m_capacity += street.capacity();
    auto const& geometry{street.geometry()};
    auto const& nodes{this->nodes()};
    if (!nodes.contains(street.source())) {
      spdlog::debug("Node with id {} not found, adding default", street.source());
      if (!geometry.empty()) {
        addNode<Intersection>(street.source(), geometry.front());
      } else {
        addNode<Intersection>(street.source());
      }
    }
    if (!nodes.contains(street.target())) {
      spdlog::debug("Node with id {} not found, adding default", street.target());
      if (!geometry.empty()) {
        addNode<Intersection>(street.target(), geometry.back());
      } else {
        addNode<Intersection>(street.target());
      }
    }
    addEdge<Street>(std::move(street));
  }

  const std::unique_ptr<Street>* RoadNetwork::street(Id source, Id destination) const {
    // Get the iterator at id m_cantorPairingHashing(source, destination)
    try {
      return &(edge(source, destination));
    } catch (const std::out_of_range&) {
      return nullptr;
    }
  }
};  // namespace dsf
