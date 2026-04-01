import cramjam
payload = (b'EasyBuild cramjam smoke test. ' * 200)

mods = ['snappy', 'lz4', 'brotli', 'bzip2', 'gzip', 'zlib', 'deflate', 'xz', 'zstd']
for name in mods:
    m = getattr(cramjam, name)
    c = m.compress(payload)
    d = bytes(m.decompress(c))
    assert d == payload, name
    print(f'[OK] {name}')

print('cramjam version:', cramjam.__version__)

try:
    import cramjam.experimental as exp
    for name in ['igzip', 'ideflate', 'izlib']:
        if hasattr(exp, name):
            m = getattr(exp, name)
            c = m.compress(payload)
            d = bytes(m.decompress(c))
            assert d == payload, name
            print(f'[OK] experimental {name}')
except Exception as e:
    print('experimental codecs unavailable:', e)

print('All OK')
