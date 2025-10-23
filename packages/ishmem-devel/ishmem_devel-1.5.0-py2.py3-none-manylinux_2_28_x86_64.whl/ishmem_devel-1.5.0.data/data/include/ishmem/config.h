/* Copyright (C) 2024 Intel Corporation
 * SPDX-License-Identifier: BSD-3-Clause
 */

#define ENABLE_MPI
#define ENABLE_OPENSHMEM
/* #undef ENABLE_PMI */
/* #undef ENABLE_ERROR_CHECKING */
/* #undef ENABLE_REDUCED_LINK_ENGINES */
#define ENABLE_DLMALLOC

/* clang-format off */
#define ISHMEM_DEFAULT_RUNTIME     ISHMEMX_RUNTIME_MPI
#define ISHMEM_DEFAULT_RUNTIME_STR "MPI"
/* clang-format on */
