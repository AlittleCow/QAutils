/**
 * Copyright (c) 2017 rxi
 *
 * This library is free software; you can redistribute it and/or modify it
 * under the terms of the MIT license. See `log.c` for details.
 */

#ifndef LOG_H
#define LOG_H

#include <stdio.h>
#include <stdarg.h>
#include <string>

#define LOG_VERSION "0.1.0"

typedef void (*log_LockFn)(void* udata, int lock);

enum LOG_LEVEL { LOG_TRACE = 1, LOG_DEBUG, LOG_INFO, LOG_WARN, LOG_ERROR, LOG_FATAL };

#define log_trace(...) log_log(LOG_TRACE, __FILE__, __LINE__, __VA_ARGS__)
#define log_debug(...) log_log(LOG_DEBUG, __FILE__, __LINE__, __VA_ARGS__)
#define log_info(...)  log_log(LOG_INFO,  __FILE__, __LINE__, __VA_ARGS__)
#define log_warn(...)  log_log(LOG_WARN,  __FILE__, __LINE__, __VA_ARGS__)
#define log_error(...) log_log(LOG_ERROR, __FILE__, __LINE__, __VA_ARGS__)
#define log_fatal(...) log_log(LOG_FATAL, __FILE__, __LINE__, __VA_ARGS__)

/**
 * @brief Set user data for the logging system
 * @param udata Pointer to user data
 */
void log_set_udata(void* udata);

/**
 * @brief Set the lock function for thread-safe logging
 * @param fn Lock function pointer
 */
void log_set_lock(log_LockFn fn);

/**
 * @brief Set the file pointer for log output
 * @param fp File pointer to write logs to
 */
void log_set_fp(FILE* fp);

/**
 * @brief Set the minimum log level
 * @param level Minimum log level to output
 */
void log_set_level(int level);

/**
 * @brief Enable or disable quiet mode (suppress stderr output)
 * @param enable 1 to enable quiet mode, 0 to disable
 */
void log_set_quiet(int enable);

/**
 * @brief Main logging function that outputs formatted log messages
 * @param level Log level for this message
 * @param file Source file name where log was called
 * @param line Line number where log was called
 * @param fmt Format string for the log message
 * @param ... Variable arguments for the format string
 */
void log_log(int level, const char* file, int line, const char* fmt, ...);

/**
 * @brief Initialize the logging system and open log file
 */
void log_init();

/**
 * @brief Close the logging system and clean up resources
 */
void log_close();

/**
 * @brief Flush the log file buffer (currently not implemented)
 */
void log_flush();

/**
 * @brief Set the log level (wrapper for log_set_level)
 * @param level Log level to set
 */
void log_set_lvl(int level);

/** @brief Global log level variable */
extern int log_level;

/**
 * @brief C++ wrapper class for logging functionality
 */
class Log {
public:
    static void Trace(const std::string& message);
    static void Debug(const std::string& message);
    static void Info(const std::string& message);
    static void Warn(const std::string& message);
    static void Error(const std::string& message);
    static void Fatal(const std::string& message);
    
    static void SetLevel(int level);
    static void SetQuiet(bool enable);
    static void Init();
    static void Close();
};

#endif