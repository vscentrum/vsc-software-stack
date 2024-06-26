local cpuarch=os.getenv("VSC_ARCH_LOCAL") or ""
if ( cpuarch == "zen4") then
    -- Automatically swap broken versions of Highway on zen4
    -- see https://github.com/google/highway/issues/1913
    module_version("Highway/1.0.5-GCCcore-12.3.0", "1.0.4-GCCcore-12.3.0")
    module_version("Highway/1.0.3-GCCcore-11.3.0", "1.0.4-GCCcore-11.3.0")
end
