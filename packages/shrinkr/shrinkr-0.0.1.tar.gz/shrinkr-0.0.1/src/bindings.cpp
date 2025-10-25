#include "compressor.hpp"
#include "compressor_factory.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl/filesystem.h>

namespace py = pybind11;

PYBIND11_MODULE(_core, m) {
  m.doc() = "Python bindings for C++ compressor project";

  py::class_<Compressor, std::shared_ptr<Compressor>>(m, "Compressor")
      .def("compress", &Compressor::compress)
      .def("decompress", &Compressor::decompress);

  py::class_<CompressorFactory>(m, "CompressorFactory")
      .def_static("create_by_name",
                  [](const std::string &name) {
                    return std::shared_ptr<Compressor>(
                        CompressorFactory::create_by_name(name).release());
                  })
      .def_static("create_by_id", [](uint8_t id) {
        return std::shared_ptr<Compressor>(
            CompressorFactory::create_by_id(id).release());
      });
}
