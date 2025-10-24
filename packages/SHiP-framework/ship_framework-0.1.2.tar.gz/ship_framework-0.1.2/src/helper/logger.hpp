#pragma once

#include <array>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>


/**
 * Use ANSI codes for colored text outputs.
 */

enum class LogLevel {
    INFO,
    WARNING,
    ERROR,
};


// Helper: Array of LogLevel-string pairs
constexpr std::array<std::pair<LogLevel, std::string_view>, 3> logLevelStrings{{
    {LogLevel::INFO, "INFO"},
    {LogLevel::WARNING, "WARNING"},
    {LogLevel::ERROR, "ERROR"},
}};


extern LogLevel CURRENT_LOG_LEVEL;

void setLogLevel(LogLevel newLevel);
void setLogLevel(const std::string& newLevel);


class Logger {
public:
    Logger(LogLevel level);

    ~Logger();

    template <typename T>
    Logger& operator<<(const T& msg) {
        if (enabled) os << msg;
        return *this;
    }

    // Overload for manipulators like std::endl
    Logger& operator<<(std::ostream& (*manip)(std::ostream&)) {
        if (enabled) os << manip;
        return *this;
    }

private:
    std::ostringstream os;
    LogLevel level;
    bool enabled;
};


#define LOG_INFO Logger(LogLevel::INFO)
#define LOG_WARN Logger(LogLevel::WARNING)
#define LOG_ERROR Logger(LogLevel::ERROR)
