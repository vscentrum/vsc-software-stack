#!/usr/bin/env bash
set -euo pipefail

expected_version="20.1.8"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

echo "== LLVM-lite smoke test =="
echo "PATH: $PATH"
echo "EBROOTLLVM: ${EBROOTLLVM:-not set}"

command -v llvm-config
llvm_config="$(command -v llvm-config)"

version="$("$llvm_config" --version)"
echo "LLVM version: $version"
test "$version" = "$expected_version"

prefix="$("$llvm_config" --prefix)"
bindir="$("$llvm_config" --bindir)"
libdir="$("$llvm_config" --libdir)"
includedir="$("$llvm_config" --includedir)"
cmakedir="$("$llvm_config" --cmakedir)"

echo "prefix:     $prefix"
echo "bindir:     $bindir"
echo "libdir:     $libdir"
echo "includedir: $includedir"
echo "cmakedir:   $cmakedir"

test -d "$prefix"
test -d "$bindir"
test -d "$libdir"
test -d "$includedir"
test -d "$cmakedir"

echo
echo "== llvm-config feature checks =="
"$llvm_config" --host-target
"$llvm_config" --targets-built
"$llvm_config" --components | tr ' ' '\n' | grep -E '^(core|support|analysis|executionengine|mcjit|native)$' || true

echo
echo "== llvmlite-style link flag check =="
"$llvm_config" --link-static --system-libs --libs core native analysis executionengine mcjit > "$tmpdir/llvmlite-link-flags.txt"
cat "$tmpdir/llvmlite-link-flags.txt"
grep -q -- '-lLLVM' "$tmpdir/llvmlite-link-flags.txt" || grep -q -- 'libLLVM' "$tmpdir/llvmlite-link-flags.txt"

echo
echo "== Core LLVM tool checks =="
for tool in llvm-as llvm-dis opt llc; do
    command -v "$tool"
    "$tool" --version | head -n 1
done

cat > "$tmpdir/add.ll" <<'EOF'
define i32 @add(i32 %a, i32 %b) {
entry:
  %sum = add i32 %a, %b
  ret i32 %sum
}
EOF

llvm-as "$tmpdir/add.ll" -o "$tmpdir/add.bc"
llvm-dis "$tmpdir/add.bc" -o "$tmpdir/add.dis.ll"
opt -passes=instcombine "$tmpdir/add.bc" -o "$tmpdir/add.opt.bc"
llc "$tmpdir/add.opt.bc" -o "$tmpdir/add.s"

test -s "$tmpdir/add.bc"
test -s "$tmpdir/add.dis.ll"
test -s "$tmpdir/add.opt.bc"
test -s "$tmpdir/add.s"

echo
echo "== CMake package discovery check =="
if command -v cmake >/dev/null 2>&1; then
    cat > "$tmpdir/CMakeLists.txt" <<'EOF'
cmake_minimum_required(VERSION 3.20)
project(test_llvm_lite CXX)
find_package(LLVM REQUIRED CONFIG)
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "LLVM_DIR=${LLVM_DIR}")
message(STATUS "LLVM_INCLUDE_DIRS=${LLVM_INCLUDE_DIRS}")
message(STATUS "LLVM_AVAILABLE_LIBS=${LLVM_AVAILABLE_LIBS}")
EOF

    cmake -S "$tmpdir" -B "$tmpdir/cmake-build" -DLLVM_DIR="$cmakedir"
else
    echo "cmake not found; skipping CMake package discovery check"
fi

echo
echo "== C++ LLVM API compile/link check =="
cat > "$tmpdir/test_llvm.cpp" <<'EOF'
#include "llvm/IR/LLVMContext.h"
#include "llvm/IR/Module.h"
#include "llvm/Support/raw_ostream.h"

int main() {
    llvm::LLVMContext context;
    llvm::Module module("easybuild_llvm_lite_test", context);
    module.print(llvm::outs(), nullptr);
    return 0;
}
EOF

cxx="${CXX:-g++}"
$cxx "$tmpdir/test_llvm.cpp" -o "$tmpdir/test_llvm" \
    $("$llvm_config" --cxxflags --ldflags --system-libs --libs core support)

"$tmpdir/test_llvm" > "$tmpdir/module.ll"
grep -q 'easybuild_llvm_lite_test' "$tmpdir/module.ll"

echo
echo "== Shared-library exposure check =="
echo "Libraries in LLVM libdir:"
find "$libdir" -maxdepth 1 \( -name 'libLLVM*.so*' -o -name 'libLLVM*.a' \) | sort | head -n 30

echo
echo "LLVM-lite smoke test passed"