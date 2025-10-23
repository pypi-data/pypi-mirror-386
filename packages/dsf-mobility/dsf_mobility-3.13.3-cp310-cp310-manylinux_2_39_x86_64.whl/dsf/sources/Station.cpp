#include "../headers/Station.hpp"

namespace dsf {
  Station::Station(Id id, Delay managementTime)
      : RoadJunction(id), m_managementTime{managementTime} {}

  Station::Station(Id id, std::pair<double, double> coords, Delay managementTime)
      : RoadJunction(id, coords), m_managementTime{managementTime} {}

  Station::Station(RoadJunction const& node, Delay managementTime)
      : RoadJunction(node), m_managementTime{managementTime} {}

  Station::Station(Station const& other)
      : RoadJunction(other),
        m_managementTime{other.m_managementTime},
        m_trains{other.m_trains} {}

  void Station::enqueue(Id trainId, train_t trainType) {
    m_trains.emplace(trainType, trainId);
  }

  Id Station::dequeue() {
    auto it = m_trains.begin();
    Id trainId = it->second;
    m_trains.erase(it);
    return trainId;
  }

  Delay Station::managementTime() const { return m_managementTime; }

  double Station::density() const {
    return static_cast<double>(m_trains.size()) / this->capacity();
  }

  bool Station::isFull() const { return m_trains.size() >= this->capacity(); }

  bool Station::isStation() const noexcept { return true; }
}  // namespace dsf