#pragma once

#include <chrono>
#include <functional>
#include <utility>

template <typename Rep = std::chrono::microseconds, typename F, typename... Args>
auto measure_runtime(F&& f, Args&&... args) {
    auto start = std::chrono::high_resolution_clock::now();
    auto result = std::invoke(std::forward<F>(f), std::forward<Args>(args)...);
    auto stop = std::chrono::high_resolution_clock::now();
    long long elapsed = std::chrono::duration_cast<Rep>(stop - start).count();
    return std::make_pair(std::move(result), elapsed);
}

template <typename Rep = std::chrono::microseconds, typename F, typename... Args>
std::enable_if_t<std::is_void_v<std::invoke_result_t<F, Args...>>, long long>
measure_runtime(F&& f, Args&&... args) {
    auto start = std::chrono::high_resolution_clock::now();
    std::invoke(std::forward<F>(f), std::forward<Args>(args)...);
    auto stop = std::chrono::high_resolution_clock::now();
    return std::chrono::duration_cast<Rep>(stop - start).count();
}
