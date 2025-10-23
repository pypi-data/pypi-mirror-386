#ifndef DFTRACER_CORE_MACRO
#define DFTRACER_CORE_MACRO

#define DFTRACER_ANY_CAST_MACRO(TYPE, VALUE, BLOCK) \
  if (auto res = any_cast_and_apply<TYPE>(VALUE)) { \
    BLOCK;                                          \
  }

#define DFTRACER_ANY_ID_MACRO(TYPE, VALUE, BLOCK) \
  if (id == typeid(TYPE)) {                       \
    BLOCK;                                        \
  }

#define DFTRACER_ANY_NUM_AGGREGATE_MACRO(TYPE, VALUE, BLOCK)           \
  if (id == typeid(TYPE)) {                                            \
    auto num_value =                                                   \
        dynamic_cast<dftracer::NumberAggregationValue<TYPE> *>(VALUE); \
    if (num_value) {                                                   \
      metadata->insert("count", num_value->count);                     \
      metadata->insert(base_key + "_sum", num_value->sum);             \
      metadata->insert(base_key + "_min", num_value->min);             \
      metadata->insert(base_key + "_max", num_value->max);             \
    }                                                                  \
    BLOCK;                                                             \
  }

#define DFTRACER_ANY_GENERAL_AGGREGATE_MACRO(TYPE, VALUE, BLOCK)             \
  if (id == typeid(TYPE)) {                                                  \
    auto num_value = dynamic_cast<dftracer::AggregatedValue<TYPE> *>(VALUE); \
    if (num_value) {                                                         \
      metadata->insert("count", num_value->count);                           \
    }                                                                        \
    BLOCK;                                                                   \
  }

#define DFTRACER_COMPARE_TYPE(TYPE, VALUE, BLOCK)            \
  if (a.type() == typeid(TYPE)) {                            \
    return std::any_cast<TYPE>(a) == std::any_cast<TYPE>(b); \
  }

#define DFTRACER_FOR_EACH_NUMERIC_TYPE(MACRO, VALUE, BLOCK) \
  MACRO(unsigned long long, VALUE, BLOCK)                   \
  MACRO(unsigned int, VALUE, BLOCK)                         \
  MACRO(double, VALUE, BLOCK)                               \
  MACRO(float, VALUE, BLOCK)                                \
  MACRO(int, VALUE, BLOCK)                                  \
  MACRO(size_t, VALUE, BLOCK)                               \
  MACRO(long, VALUE, BLOCK)                                 \
  MACRO(uint16_t, VALUE, BLOCK)                             \
  MACRO(ssize_t, VALUE, BLOCK)                              \
  MACRO(off_t, VALUE, BLOCK)                                \
  MACRO(mode_t, VALUE, BLOCK)                               \
  MACRO(off64_t, VALUE, BLOCK)

#define DFTRACER_FOR_EACH_STRING_TYPE(MACRO, VALUE, BLOCK) \
  MACRO(const char *, VALUE, BLOCK)                        \
  MACRO(HashType, VALUE, BLOCK)                            \
  MACRO(std::string, VALUE, BLOCK)

#define DFTRACER_NUM_AGGREGATE(OBJ, CLASS, TYPE) \
  dynamic_cast<CLASS<TYPE> *>(OBJ)->update(dynamic_cast<CLASS<TYPE> *>(value));
#endif  // DFTRACER_CORE_MACRO
