#ifndef DFTRACER_CORE_DATASTRUCTURE_H
#define DFTRACER_CORE_DATASTRUCTURE_H

// Internal
#include <dftracer/core/common/cpp_typedefs.h>
#include <dftracer/core/common/enumeration.h>
#include <dftracer/core/common/logging.h>
#include <dftracer/core/common/macros.h>
#include <dftracer/core/common/typedef.h>

// standard headers
#include <stddef.h>

#include <any>
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <typeindex>
#include <typeinfo>
#include <unordered_map>
#include <variant>
#include <vector>

namespace dftracer {

class Metadata {
 private:
  typedef std::unordered_map<std::string, std::pair<MetadataType, std::any>>
      DataMap;
  DataMap data;

 public:
  Metadata() {}
  ~Metadata() {}
  std::pair<DataMap::iterator, bool> insert_or_assign(const std::string &key,
                                                      const std::any &value) {
    auto ret =
        data.insert_or_assign(key, std::make_pair(MetadataType::MT_KEY, value));
    return ret;
  }
  std::pair<DataMap::iterator, bool> insert_or_assign(
      const std::string &key, const std::any &value, const MetadataType &type) {
    auto ret = data.insert_or_assign(key, std::make_pair(type, value));
    return ret;
  }
  bool contains(const std::string &key) const {
    return data.find(key) != data.end();
  }

  size_t erase(const std::string &key) { return data.erase(key); }

  size_t size() const { return data.size(); }

  bool empty() const { return data.empty(); }

  void clear() { data.clear(); }

  std::pair<DataMap::iterator, bool> insert(const std::string &key,
                                            const std::any &value) {
    return data.insert({key, std::make_pair(MetadataType::MT_KEY, value)});
  }
  std::pair<DataMap::iterator, bool> insert(const std::string &key,
                                            const std::any &value,
                                            const MetadataType &type) {
    return data.insert({key, std::make_pair(type, value)});
  }

  DataMap::iterator find(const std::string &key) { return data.find(key); }

  DataMap::const_iterator find(const std::string &key) const {
    return data.find(key);
  }

  std::pair<MetadataType, std::any> &operator[](const std::string &key) {
    return data[key];
  }

  const std::pair<MetadataType, std::any> &at(const std::string &key) const {
    return data.at(key);
  }

  DataMap::iterator begin() { return data.begin(); }

  DataMap::const_iterator begin() const { return data.begin(); }

  DataMap::iterator end() { return data.end(); }

  DataMap::const_iterator end() const { return data.end(); }

  std::string getTagValue(const std::string &tagKey) const;
};

inline bool compare_any(const std::any &a, const std::any &b) {
  if (a.type() != b.type()) return false;
  DFTRACER_FOR_EACH_NUMERIC_TYPE(DFTRACER_COMPARE_TYPE, NULL,
                                 { return result; })
  DFTRACER_FOR_EACH_STRING_TYPE(DFTRACER_COMPARE_TYPE, NULL, { return result; })
  return false;
}

struct AggregatedKey {
  std::string category;
  std::string event_name;
  TimeResolution time_interval;
  ThreadID thread_id;
  Metadata *additional_keys;
  /* These attributes are just holder for rules not used in aggregation-key */
  TimeResolution duration;
  const char *app_name;
  const int *rank;

  AggregatedKey()
      : category(nullptr),
        event_name(nullptr),
        time_interval(0),
        thread_id(0),
        additional_keys(nullptr),
        duration(0),
        app_name(nullptr),
        rank(nullptr) {}

  AggregatedKey(ConstEventNameType category_, ConstEventNameType event_name_,
                TimeResolution time_interval_, TimeResolution duration_,
                ThreadID thread_id_, Metadata *metadata_, const char *app_name_,
                const int *rank_)
      : category(category_),
        event_name(event_name_),
        time_interval(time_interval_),
        thread_id(thread_id_),
        additional_keys(metadata_),
        duration(duration_),
        app_name(app_name_),
        rank(rank_) {}
  AggregatedKey(const AggregatedKey &other)
      : category(other.category),
        event_name(other.event_name),
        time_interval(other.time_interval),
        thread_id(other.thread_id),
        additional_keys(other.additional_keys),
        duration(other.duration),
        app_name(other.app_name),
        rank(other.rank) {}
  bool operator==(const AggregatedKey &other) const {
    return category == other.category && event_name == other.event_name &&
           time_interval == other.time_interval &&
           thread_id == other.thread_id &&
           additional_keys == other.additional_keys;

    // Compare additional_keys for MetadataType::MT_KEY
    if (additional_keys && other.additional_keys) {
      for (const auto &pair : *additional_keys) {
        if (pair.second.first == MetadataType::MT_KEY) {
          auto it = other.additional_keys->find(pair.first);
          if (it == other.additional_keys->end() ||
              it->second.first != MetadataType::MT_KEY ||
              it->second.second.type() != pair.second.second.type() ||
              compare_any(it->second.second, pair.second.second)) {
            return false;
          }
        }
      }
      for (const auto &pair : *other.additional_keys) {
        if (pair.second.first == MetadataType::MT_KEY) {
          auto it = additional_keys->find(pair.first);
          if (it == additional_keys->end() ||
              it->second.first != MetadataType::MT_KEY ||
              it->second.second.type() != pair.second.second.type() ||
              compare_any(it->second.second, pair.second.second)) {
            return false;
          }
        }
      }
    } else if (additional_keys || other.additional_keys) {
      // One is nullptr, the other is not
      return false;
    }
  }
};

// Specialize std::hash for AggregatedKey
}  // namespace dftracer

namespace std {
template <>
struct hash<dftracer::AggregatedKey> {
  std::size_t operator()(const dftracer::AggregatedKey &key) const {
    std::size_t h1 = std::hash<std::string>()(key.category);
    std::size_t h2 = std::hash<std::string>()(key.event_name);
    std::size_t h3 = std::hash<TimeResolution>()(key.time_interval);
    std::size_t h4 = std::hash<ThreadID>()(key.thread_id);

    std::size_t h5 = 0;
    if (key.additional_keys) {
      for (const auto &pair : *key.additional_keys) {
        if (pair.second.first == MetadataType::MT_KEY) {
          h5 ^= std::hash<std::string>()(pair.first);
          // For std::any, we can only hash the type info
          h5 ^= pair.second.second.type().hash_code();
        }
      }
    }

    // Combine hashes
    std::size_t result = h1;
    result ^= h2 + 0x9e3779b9 + (result << 6) + (result >> 2);
    result ^= h3 + 0x9e3779b9 + (result << 6) + (result >> 2);
    result ^= h4 + 0x9e3779b9 + (result << 6) + (result >> 2);
    result ^= h5 + 0x9e3779b9 + (result << 6) + (result >> 2);

    return result;
  }
};
}  // namespace std

namespace dftracer {

struct BaseAggregatedValue {
 public:
  BaseAggregatedValue *_child;
  ValueType _type;
  std::type_index _id;

 protected:
  BaseAggregatedValue(BaseAggregatedValue *child, ValueType type,
                      std::type_index id)
      : _child(child), _type(type), _id(id) {}

 public:
  virtual ~BaseAggregatedValue() = default;
  void update(BaseAggregatedValue *value);
  BaseAggregatedValue *get_value();
};

template <typename T>
struct AggregatedValue : public BaseAggregatedValue {
 protected:
  AggregatedValue(const AggregatedValue<T> &value, BaseAggregatedValue *child)
      : BaseAggregatedValue(child, ValueType::VALUE_TYPE_STRING, typeid(T)),
        count(value.count) {}
  AggregatedValue(const AggregatedValue<T> &value, BaseAggregatedValue *child,
                  ValueType id, std::type_index tid)
      : BaseAggregatedValue(child, id, tid), count(value.count) {}
  AggregatedValue(BaseAggregatedValue *child, ValueType id, std::type_index tid)
      : BaseAggregatedValue(child, id, tid), count(1) {}

 public:
  size_t count;
  void update(AggregatedValue<T> *value) { count += value->count; }
  AggregatedValue(T value)
      : BaseAggregatedValue(this, ValueType::VALUE_TYPE_STRING, typeid(T)),
        count(1) {}
};

template <typename T>
struct NumberAggregationValue : public AggregatedValue<T> {
 public:
  T min, max, sum;
  NumberAggregationValue(NumberAggregationValue<T> &value)
      : AggregatedValue<T>(value, this, ValueType::VALUE_TYPE_NUMBER,
                           typeid(T)),
        min(value.min),
        max(value.max),
        sum(value.sum) {}
  NumberAggregationValue(T value)
      : AggregatedValue<T>(this, ValueType::VALUE_TYPE_NUMBER, typeid(T)),
        min(value),
        max(value),
        sum(value) {}
  void update(NumberAggregationValue<T> *value) {
    if (value->min < min) min = value->min;
    if (value->max > max) max = value->max;
    sum += value->sum;
    AggregatedValue<T>::update(value);
  }
};

class AggregatedValues {
 public:
  AggregatedValues() {}
  ~AggregatedValues() {}
  std::unordered_map<std::string, BaseAggregatedValue *> values;
  int update(const std::string &key, const std::type_info &id,
             BaseAggregatedValue *value) {
    auto it = values.find(key);
    if (it != values.end()) {
      it->second->update(value);
      delete value;
    } else {
      values.insert_or_assign(key, value);
    }
    return 0;
  }
};

struct Value {
  std::variant<std::string, TimeResolution, double, std::set<std::string>> data;
};

struct Field {
  std::vector<std::string>
      path;  // e.g., tags.performance -> ["tags", "performance"]
};

struct RuleAST {
  // AST Node
  struct Node {
    virtual ~Node() = default;
  };

  struct BinaryOp : Node {
    RuleOp op;
    std::unique_ptr<Node> left;
    std::unique_ptr<Node> right;
    BinaryOp(RuleOp op, std::unique_ptr<Node> l, std::unique_ptr<Node> r)
        : op(op), left(std::move(l)), right(std::move(r)) {}
  };

  struct UnaryOp : Node {
    RuleOp op;
    std::unique_ptr<Node> operand;
    UnaryOp(RuleOp op, std::unique_ptr<Node> operand)
        : op(op), operand(std::move(operand)) {}
  };

  struct Comparison : Node {
    RuleOp op;
    Field field;
    Value value;
    Comparison(RuleOp op, Field field, Value value)
        : op(op), field(std::move(field)), value(std::move(value)) {}
  };

  struct InOp : Node {
    Field field;
    std::set<std::string> values;
    InOp(Field field, std::set<std::string> values)
        : field(std::move(field)), values(std::move(values)) {}
  };

  struct LikeOp : Node {
    Field field;
    std::string pattern;
    LikeOp(Field field, std::string pattern)
        : field(std::move(field)), pattern(std::move(pattern)) {}
  };

  std::unique_ptr<Node> root;
};

// Helper functions for field extraction and comparison
inline std::optional<Value> getFieldValue(const AggregatedKey *key,
                                          const Field &field) {
  // Extract field value from AggregatedKey based on field.path
  if (!key || field.path.empty()) return std::nullopt;
  const std::string &fieldName = field.path[0];

  if (fieldName == "cat") {
    return Value{key->category};
  } else if (fieldName == "name") {
    return Value{key->event_name};
  } else if (fieldName == "ts") {
    return Value{key->time_interval};
  } else if (fieldName == "dur") {
    return Value{key->duration};
  } else if (fieldName == "app" && key->app_name != nullptr) {
    return Value{key->app_name};
  } else if (fieldName == "rank" && *key->rank != -1) {
    return Value{(TimeResolution)*key->rank};
  } else if (fieldName.rfind("tags.", 0) == 0 && key->additional_keys) {
    // tags.<tagname>
    std::string tagKey = fieldName.substr(5);
    std::string tagValue = key->additional_keys->getTagValue(tagKey);
    return Value{tagValue};
  }
  return std::nullopt;
}

inline bool compareValues(const Value &lhs, const Value &rhs, RuleOp op) {
  if (lhs.data.index() != rhs.data.index()) return false;
  if (std::holds_alternative<TimeResolution>(lhs.data)) {
    int l = std::get<TimeResolution>(lhs.data);
    int r = std::get<TimeResolution>(rhs.data);
    switch (op) {
      case RuleOp::EQ:
        return l == r;
      case RuleOp::NEQ:
        return l != r;
      case RuleOp::GT:
        return l > r;
      case RuleOp::LT:
        return l < r;
      case RuleOp::GTE:
        return l >= r;
      case RuleOp::LTE:
        return l <= r;
      default:
        return false;
    }
  }
  if (std::holds_alternative<double>(lhs.data)) {
    double l = std::get<double>(lhs.data);
    double r = std::get<double>(rhs.data);
    switch (op) {
      case RuleOp::EQ:
        return l == r;
      case RuleOp::NEQ:
        return l != r;
      case RuleOp::GT:
        return l > r;
      case RuleOp::LT:
        return l < r;
      case RuleOp::GTE:
        return l >= r;
      case RuleOp::LTE:
        return l <= r;
      default:
        return false;
    }
  }
  if (std::holds_alternative<std::string>(lhs.data)) {
    const std::string &l = std::get<std::string>(lhs.data);
    const std::string &r = std::get<std::string>(rhs.data);
    switch (op) {
      case RuleOp::EQ:
        return l == r;
      case RuleOp::NEQ:
        return l != r;
      default:
        return false;
    }
  }
  return false;
}

inline bool likeMatch(const std::string &value, const std::string &pattern) {
  // Handles patterns: "*stat", "*stat*", "stat*"
  if (pattern == "*") return true;  // matches anything

  size_t first_star = pattern.find('*');
  size_t last_star = pattern.rfind('*');

  if (first_star == std::string::npos) {
    // No wildcard, exact match
    return value == pattern;
  }

  if (first_star == 0 && last_star == pattern.size() - 1 &&
      pattern.size() > 1) {
    // Pattern: *stat*
    std::string inner = pattern.substr(1, pattern.size() - 2);
    return value.find(inner) != std::string::npos;
  }

  if (first_star == 0) {
    // Pattern: *stat
    std::string suffix = pattern.substr(1);
    return value.size() >= suffix.size() &&
           value.compare(value.size() - suffix.size(), suffix.size(), suffix) ==
               0;
  }

  if (last_star == pattern.size() - 1) {
    // Pattern: stat*
    std::string prefix = pattern.substr(0, pattern.size() - 1);
    return value.size() >= prefix.size() &&
           value.compare(0, prefix.size(), prefix) == 0;
  }

  // Fallback: only support single '*' at start or end or both
  return false;
}
}  // namespace dftracer

#endif  // DFTRACER_CORE_DATASTRUCTURE_H
