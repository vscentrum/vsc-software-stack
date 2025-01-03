add_executable(translator
  translator.cc
  )
target_include_directories(translator
  PRIVATE "$ENV{EBROOTCXXOPTS}/include"
)
target_link_libraries(translator
  PRIVATE ${PROJECT_NAME}
)

set_target_properties(translator PROPERTIES OUTPUT_NAME ct2-translator)

install(
  TARGETS translator
  DESTINATION ${CMAKE_INSTALL_BINDIR}
  )