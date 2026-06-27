cmake_minimum_required(VERSION 3.16)

file(GLOB_RECURSE SOURCES CONFIGURE_DEPENDS *.cpp *.hpp *.qrc)

find_package(Qt6 REQUIRED COMPONENTS Widgets Network Sql)

add_executable(ai-ide ${SOURCES})
target_link_libraries(ai-ide PRIVATE Qt6::Widgets Qt6::Network Qt6::Sql)

# Helps IntelliSense find headers in subdirectories like ui/ or ai/
target_include_directories(ai-ide PRIVATE 
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_compile_definitions(ai-ide PRIVATE
    QT_DEPRECATED_WARNINGS
)
