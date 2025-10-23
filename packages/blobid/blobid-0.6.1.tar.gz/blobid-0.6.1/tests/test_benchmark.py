import blobid as bi


def test_bench_base(benchmark, fs_vof_small):
    benchmark(bi.get_labels,
              void_fraction=fs_vof_small,
              periodic=[False, False, False]
              )


def test_bench_WY(benchmark, fs_vof_small):
    benchmark(bi.get_labels,
              void_fraction=fs_vof_small,
              periodic=[False, False, False],
              normals_method='WY'
              )


def test_bench_no_norm(benchmark, fs_vof_small):
    benchmark(bi.get_labels,
              void_fraction=fs_vof_small,
              periodic=[False, False, False],
              use_normals=False
              )


def test_bench_Chan(benchmark, fs_vof_small):
    benchmark(bi.get_labels,
              void_fraction=fs_vof_small,
              periodic=[False, False, False],
              use_normals=False,
              cutoff=0.5,
              cutoff_method='neighbors'
              )
