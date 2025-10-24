#include "logger.hpp"

#include <pch.hpp>


LogLevel CURRENT_LOG_LEVEL = LogLevel::WARNING;


void setLogLevel(LogLevel newLevel) {
    CURRENT_LOG_LEVEL = newLevel;
}

void setLogLevel(const std::string& newLevel) {
    for (const auto& [key, value] : logLevelStrings) {
        if (to_lower(std::string(value)) == to_lower(newLevel)) {
            CURRENT_LOG_LEVEL = key;
            return;
        }
    }
    LOG_ERROR << "Invalid log level: " << newLevel << std::endl
              << "Available log levels: INFO, WARNING, ERROR";
    throw std::invalid_argument("Invalid log level");
}


Logger::Logger(LogLevel level) : level(level), enabled(level >= CURRENT_LOG_LEVEL) {
    if (!enabled) return;

    switch (level) {
        case LogLevel::INFO: {
            os << "\033[1;32m[INFO] ";
            break;
        }
        case LogLevel::WARNING: {
            os << "\033[0;33m[WARNING] ";
            break;
        }
        case LogLevel::ERROR: {
            os << "\033[0;31m[ERROR] ";
            break;
        }
    }
}

Logger::~Logger() {
    if (!enabled) return;
    os << "\033[0m" << std::endl;
    if (level == LogLevel::ERROR) {
        std::cerr << os.str();
        std::cerr.flush();
    } else {
        std::cout << os.str();
        std::cout.flush();
    }
}
