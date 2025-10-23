#ifdef __cplusplus
extern "C" {
#endif
#define CPP_LOGGER_PRINT 1
#define CPP_LOGGER_ERROR 2
#define CPP_LOGGER_WARN 3
#define CPP_LOGGER_INFO 4
#define CPP_LOGGER_DEBUG 5
#define CPP_LOGGER_TRACE 6
#include <stdio.h>
extern void cpp_logger_clog(const int logger_level, const char* name, const char* string,
                 ...);
extern void cpp_logger_clog_level(const int logger_level, const char* name);
extern void cpp_logger_clog_level_file(const int logger_level, const char* name, FILE* file);
#ifdef __cplusplus
}
#endif
