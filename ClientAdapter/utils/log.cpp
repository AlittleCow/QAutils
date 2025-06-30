/*
 * Copyright (c) 2017 rxi
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */

#ifdef _WIN32
#include <windows.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <time.h>

#include <share.h>
#include <string>
#include "log.h"

#pragma warning( disable : 4996)

using namespace std;

static struct {
    void* udata;
    log_LockFn lock;
    FILE* fp = NULL;
    int level = 0;
    int quiet;
} L;

static const char* level_names[] = {
  "TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"
};

#ifdef LOG_USE_COLOR
static const char* level_colors[] = {
  "\x1b[94m", "\x1b[36m", "\x1b[32m", "\x1b[33m", "\x1b[31m", "\x1b[35m"
};
#endif

/**
 * @brief Acquire a lock if a lock function is set
 */
static void inline lock(void) {
    if (L.lock) {
        L.lock(L.udata, 1);
    }
}

/**
 * @brief Release a lock if a lock function is set
 */
static void inline unlock(void) {
    if (L.lock) {
        L.lock(L.udata, 0);
    }
}

/**
 * @brief Set user data for the logging system
 * @param udata Pointer to user data
 */
void log_set_udata(void* udata) {
    L.udata = udata;
}

/**
 * @brief Set the lock function for thread-safe logging
 * @param fn Lock function pointer
 */
void log_set_lock(log_LockFn fn) {
    L.lock = fn;
}

/**
 * @brief Set the file pointer for log output
 * @param fp File pointer to write logs to
 */
void log_set_fp(FILE* fp) {
    L.fp = fp;
}

/**
 * @brief Set the minimum log level
 * @param level Minimum log level to output
 */
void log_set_level(int level) {
    L.level = level;
    log_level = level;
}

/**
 * @brief Enable or disable quiet mode (suppress stderr output)
 * @param enable 1 to enable quiet mode, 0 to disable
 */
void log_set_quiet(int enable) {
    L.quiet = enable ? 1 : 0;
}

/** @brief Global log level variable */
int log_level = LOG_LEVEL::LOG_FATAL;

/**
 * @brief Extract the last two directory levels from a file path
 * @param filepath The full file path
 * @return A string containing the last two directory levels and filename
 */
static const char* extract_last_two_levels(const char* filepath) {
    static char result[256];
    const char* p = filepath;
    const char* last_slash = nullptr;
    const char* second_last_slash = nullptr;
    
    // Find the last directory separator
    while (*p) {
        if (*p == '\\' || *p == '/') {
            second_last_slash = last_slash;
            last_slash = p;
        }
        p++;
    }
    
    // If we found at least two directory separators, start from the second-to-last
    if (second_last_slash != nullptr) {
        strncpy(result, second_last_slash + 1, sizeof(result) - 1);
        result[sizeof(result) - 1] = '\0';
        return result;
    }
    // If we found only one separator, start from the last one
    else if (last_slash != nullptr) {
        strncpy(result, last_slash + 1, sizeof(result) - 1);
        result[sizeof(result) - 1] = '\0';
        return result;
    }
    // If no separators found, return the original filepath
    else {
        return filepath;
    }
}

/**
 * @brief Main logging function that outputs formatted log messages
 * @param level Log level for this message
 * @param file Source file name where log was called
 * @param line Line number where log was called
 * @param fmt Format string for the log message
 * @param ... Variable arguments for the format string
 */
void log_log(int level, const char* file, int line, const char* fmt, ...) {

    if (level < L.level || L.fp == NULL) {
        return;
    }
    /* Acquire lock */
    lock();

    /* Get current time */
    struct tm lt;   //tm结构指针
    time_t now;  //声明time_t类型变量
    time(&now);      //获取系统日期和时间
    localtime_s(&lt, &now);   //获取当地日期和时间

    // Extract short file path for cleaner output
    const char* short_file = extract_last_two_levels(file);

    /* Log to stderr */
#if 0
    if (!L.quiet) {
        va_list args;
        char buf[16];
        buf[strftime(buf, sizeof(buf), "%H:%M:%S", &lt)] = '\0';
#ifdef LOG_USE_COLOR
        fprintf(
            stderr, "%s %s%-5s\x1b[0m \x1b[90m%s:%d:\x1b[0m ",
            buf, level_colors[level], level_names[level], short_file, line);
#else
        fprintf(stderr, "%s %-5s %s:%d: ", buf, level_names[level], short_file, line);
#endif
        va_start(args, fmt);
        vfprintf(stderr, fmt, args);
        va_end(args);
        fprintf(stderr, "\n");
        fflush(stderr);
    }
#endif

    /* Log to file */
    if (L.fp) {
        va_list args;
        char buf[32];
        buf[strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &lt)] = '\0';
        fprintf(L.fp, "%s %-5s %s:%d: ", buf, level_names[level], short_file, line);
        va_start(args, fmt);
        vfprintf(L.fp, fmt, args);
        va_end(args);
        fprintf(L.fp, "\n");
        fflush(L.fp);
    }

    /* Release lock */
    unlock();
}

///added
#define USE_LOGFILE 1

/** @brief Global file pointer for log file */
FILE* Logfp = NULL;

/**
 * @brief Initialize the logging system and open log file
 */
void log_init()
{
    if (Logfp == NULL)
    {

#ifdef USE_LOGFILE
        //fopen_s(&Logfp,"./app_log.dat", "wb+");
        //Logfp = _fsopen("C:\\Users\\lab\\app_log.dat", "wb+", _SH_DENYNO);
 
        char buffer[MAX_PATH];
        GetModuleFileNameA(NULL, buffer, MAX_PATH);
        string::size_type pos = string(buffer).find_last_of("\\/");
        string currentPath = string(buffer).substr(0, pos);
        char fullPath[MAX_PATH];
        sprintf(fullPath, "%s\\%s", currentPath.c_str(), "app_log.dat");

        
        Logfp = _fsopen(fullPath, "wb+", _SH_DENYNO);
        if (Logfp == NULL)
            return;

        log_set_fp(Logfp);

        log_info("Hi,log inited! @ %s",fullPath);

#endif
    }
}

/**
 * @brief Close the logging system and clean up resources
 */
void log_close()
{
    log_trace("log close.");

    if (Logfp)
    {
        fclose(Logfp);
        Logfp = NULL;
    }

}

/**
 * @brief Flush the log file buffer (currently not implemented)
 */
void log_flush()
{
    //if (Logfp)
    //    fflush(Logfp);
}

/**
 * @brief Set the log level (wrapper for log_set_level)
 * @param level Log level to set
 */
void log_set_lvl(int level)
{
    log_set_level(level);
}
