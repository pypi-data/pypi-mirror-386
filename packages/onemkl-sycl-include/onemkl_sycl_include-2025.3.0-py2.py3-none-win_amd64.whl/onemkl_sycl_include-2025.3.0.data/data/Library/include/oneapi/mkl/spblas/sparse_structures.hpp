/*******************************************************************************
* Copyright (C) 2019 Intel Corporation
*
* This software and the related documents are Intel copyrighted  materials,  and
* your use of  them is  governed by the  express license  under which  they were
* provided to you (License).  Unless the License provides otherwise, you may not
* use, modify, copy, publish, distribute,  disclose or transmit this software or
* the related documents without Intel's prior written permission.
*
* This software and the related documents  are provided as  is,  with no express
* or implied  warranties,  other  than those  that are  expressly stated  in the
* License.
*******************************************************************************/

#ifndef _ONEMKL_SPARSE_STRUCTURES_HPP_
#define _ONEMKL_SPARSE_STRUCTURES_HPP_

#include <sycl/sycl.hpp>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <stdexcept>

#include "oneapi/mkl/export.hpp"
#include "oneapi/mkl/types.hpp"
#include "oneapi/mkl/exceptions.hpp"

namespace oneapi {
namespace mkl {
namespace sparse {

/******************************************************************************/
struct matrix_handle;
typedef struct matrix_handle *matrix_handle_t;

DLL_EXPORT void init_matrix_handle(matrix_handle_t *p_spmat);

// non-blocking version of release_matrix_handle, will schedule clean up of handle
// asychronously pending dependencies and return an event to track it
DLL_EXPORT sycl::event
release_matrix_handle(sycl::queue &queue,
                      matrix_handle_t *p_spmat,
                      const std::vector<sycl::event> &dependencies = {});

/******************************************************************************/
//
// PROPERTY of matrix arrays/data. The property must be consistent with the
// data; this consistency is not verified and assumed to be true when provided
// by the user for performance reasons. If user-supplied data properties are
// inconsistent from actual matrix arrays/data, then applications may
// crash/hang/produce incorrect results.
enum class property : char {
    symmetric = 0,
    sorted    = 1,
};

DLL_EXPORT void set_matrix_property(matrix_handle_t spmat, property property_value);

/******************************************************************************/
#define ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_CSR_DATA(IntType, FpType) \
    [[deprecated("Use oneapi::mkl::sparse::set_csr_data(queue, spmat, nrows, ncols, nnz, ...) instead.")]] \
    DLL_EXPORT void set_csr_data(sycl::queue &queue, \
                                 matrix_handle_t spmat, \
                                 const IntType nrows, \
                                 const IntType ncols, \
                                 index_base index, \
                                 sycl::buffer<IntType, 1> &row_ptr, \
                                 sycl::buffer<IntType, 1> &col_ind, \
                                 sycl::buffer<FpType, 1> &values); \
    [[deprecated("Use oneapi::mkl::sparse::set_csr_data(queue, spmat, nrows, ncols, nnz, ...) instead.")]] \
    DLL_EXPORT sycl::event set_csr_data(sycl::queue &queue, \
                                        matrix_handle_t spmat, \
                                        const IntType nrows, \
                                        const IntType ncols, \
                                        index_base index, \
                                        IntType *row_ptr, \
                                        IntType *col_ind, \
                                        FpType *values, \
                                        const std::vector<sycl::event> &dependencies = {})

ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_CSR_DATA(std::int32_t, float);
ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_CSR_DATA(std::int32_t, double);
ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_CSR_DATA(std::int32_t, std::complex<float>);
ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_CSR_DATA(std::int32_t, std::complex<double>);
ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_CSR_DATA(std::int64_t, float);
ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_CSR_DATA(std::int64_t, double);
ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_CSR_DATA(std::int64_t, std::complex<float>);
ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_CSR_DATA(std::int64_t, std::complex<double>);

#undef ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_CSR_DATA

/******************************************************************************/
#define ONEMKL_DECLARE_SPARSE_SET_CSR_DATA(IntType, FpType) \
    DLL_EXPORT void set_csr_data(sycl::queue &queue, \
                                 matrix_handle_t spmat, \
                                 const std::int64_t nrows, \
                                 const std::int64_t ncols, \
                                 const std::int64_t nnz, \
                                 index_base index, \
                                 sycl::buffer<IntType, 1> &row_ptr, \
                                 sycl::buffer<IntType, 1> &col_ind, \
                                 sycl::buffer<FpType, 1> &values); \
    DLL_EXPORT sycl::event set_csr_data(sycl::queue &queue, \
                                        matrix_handle_t spmat, \
                                        const std::int64_t nrows, \
                                        const std::int64_t ncols, \
                                        const std::int64_t nnz, \
                                        index_base index, \
                                        IntType *row_ptr, \
                                        IntType *col_ind, \
                                        FpType *values, \
                                        const std::vector<sycl::event> &dependencies = {})

ONEMKL_DECLARE_SPARSE_SET_CSR_DATA(std::int32_t, float);
ONEMKL_DECLARE_SPARSE_SET_CSR_DATA(std::int32_t, double);
ONEMKL_DECLARE_SPARSE_SET_CSR_DATA(std::int32_t, std::complex<float>);
ONEMKL_DECLARE_SPARSE_SET_CSR_DATA(std::int32_t, std::complex<double>);
ONEMKL_DECLARE_SPARSE_SET_CSR_DATA(std::int64_t, float);
ONEMKL_DECLARE_SPARSE_SET_CSR_DATA(std::int64_t, double);
ONEMKL_DECLARE_SPARSE_SET_CSR_DATA(std::int64_t, std::complex<float>);
ONEMKL_DECLARE_SPARSE_SET_CSR_DATA(std::int64_t, std::complex<double>);

#undef ONEMKL_DECLARE_SPARSE_SET_CSR_DATA

/******************************************************************************/
#define ONEMKL_DECLARE_SPARSE_SET_CSC_DATA(IntType, FpType) \
    DLL_EXPORT void set_csc_data(sycl::queue &queue, \
                                 matrix_handle_t spMat, \
                                 const std::int64_t nrows, \
                                 const std::int64_t ncols, \
                                 const std::int64_t nnz, \
                                 index_base index, \
                                 sycl::buffer<IntType, 1> &col_ptr, \
                                 sycl::buffer<IntType, 1> &row_ind, \
                                 sycl::buffer<FpType, 1> &values); \
    DLL_EXPORT sycl::event set_csc_data(sycl::queue &queue, \
                                        matrix_handle_t spMat, \
                                        const std::int64_t nrows, \
                                        const std::int64_t ncols, \
                                        const std::int64_t nnz, \
                                        index_base index, \
                                        IntType *col_ptr, \
                                        IntType *row_ind, \
                                        FpType *values, \
                                        const std::vector<sycl::event> &dependencies = {})

ONEMKL_DECLARE_SPARSE_SET_CSC_DATA(std::int32_t, float);
ONEMKL_DECLARE_SPARSE_SET_CSC_DATA(std::int32_t, double);
ONEMKL_DECLARE_SPARSE_SET_CSC_DATA(std::int32_t, std::complex<float>);
ONEMKL_DECLARE_SPARSE_SET_CSC_DATA(std::int32_t, std::complex<double>);
ONEMKL_DECLARE_SPARSE_SET_CSC_DATA(std::int64_t, float);
ONEMKL_DECLARE_SPARSE_SET_CSC_DATA(std::int64_t, double);
ONEMKL_DECLARE_SPARSE_SET_CSC_DATA(std::int64_t, std::complex<float>);
ONEMKL_DECLARE_SPARSE_SET_CSC_DATA(std::int64_t, std::complex<double>);

#undef ONEMKL_DECLARE_SPARSE_SET_CSC_DATA

/******************************************************************************/
#define ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_COO_DATA(IntType, FpType) \
    [[deprecated("Use oneapi::mkl::sparse::set_coo_data(sycl::queue &queue, matrix_handle_t spmat, const std::int64_t nrows, ...) instead.")]] \
    DLL_EXPORT void set_coo_data(sycl::queue &queue, \
                                 matrix_handle_t spmat, \
                                 const IntType nrows, \
                                 const IntType ncols, \
                                 const IntType nnz, \
                                 index_base index, \
                                 sycl::buffer<IntType, 1> &row_ind, \
                                 sycl::buffer<IntType, 1> &col_ind, \
                                 sycl::buffer<FpType, 1> &values); \
    [[deprecated("Use oneapi::mkl::sparse::set_coo_data(sycl::queue &queue, matrix_handle_t spmat, const std::int64_t nrows, ...) instead.")]] \
    DLL_EXPORT sycl::event set_coo_data(sycl::queue &queue, \
                                        matrix_handle_t spmat, \
                                        const IntType nrows, \
                                        const IntType ncols, \
                                        const IntType nnz, \
                                        index_base index, \
                                        IntType *row_ind, \
                                        IntType *col_ind, \
                                        FpType *values, \
                                        const std::vector<sycl::event> &dependencies = {})

ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_COO_DATA(std::int32_t, float);
ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_COO_DATA(std::int32_t, double);
ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_COO_DATA(std::int32_t, std::complex<float>);
ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_COO_DATA(std::int32_t, std::complex<double>);

#undef ONEMKL_DECLARE_DEPRECATED_SPARSE_SET_COO_DATA

/******************************************************************************/
#define ONEMKL_DECLARE_SPARSE_SET_COO_DATA(IntType, FpType) \
    DLL_EXPORT void set_coo_data(sycl::queue &queue, \
                                 matrix_handle_t spmat, \
                                 const std::int64_t nrows, \
                                 const std::int64_t ncols, \
                                 const std::int64_t nnz, \
                                 index_base index, \
                                 sycl::buffer<IntType, 1> &row_ind, \
                                 sycl::buffer<IntType, 1> &col_ind, \
                                 sycl::buffer<FpType, 1> &values); \
    DLL_EXPORT sycl::event set_coo_data(sycl::queue &queue, \
                                        matrix_handle_t spmat, \
                                        const std::int64_t nrows, \
                                        const std::int64_t ncols, \
                                        const std::int64_t nnz, \
                                        index_base index, \
                                        IntType *row_ind, \
                                        IntType *col_ind, \
                                        FpType *values, \
                                        const std::vector<sycl::event> &dependencies = {})

ONEMKL_DECLARE_SPARSE_SET_COO_DATA(std::int32_t, float);
ONEMKL_DECLARE_SPARSE_SET_COO_DATA(std::int32_t, double);
ONEMKL_DECLARE_SPARSE_SET_COO_DATA(std::int32_t, std::complex<float>);
ONEMKL_DECLARE_SPARSE_SET_COO_DATA(std::int32_t, std::complex<double>);
ONEMKL_DECLARE_SPARSE_SET_COO_DATA(std::int64_t, float);
ONEMKL_DECLARE_SPARSE_SET_COO_DATA(std::int64_t, double);
ONEMKL_DECLARE_SPARSE_SET_COO_DATA(std::int64_t, std::complex<float>);
ONEMKL_DECLARE_SPARSE_SET_COO_DATA(std::int64_t, std::complex<double>);

#undef ONEMKL_DECLARE_SPARSE_SET_COO_DATA

/******************************************************************************/
#define ONEMKL_DECLARE_SPARSE_SET_BSR_DATA(IntType, FpType) \
    DLL_EXPORT void set_bsr_data(sycl::queue &queue, \
                                 matrix_handle_t spmat, \
                                 const std::int64_t blk_nrows, \
                                 const std::int64_t blk_ncols, \
                                 const std::int64_t blk_nnz, \
                                 const std::int64_t row_blk_size, \
                                 const std::int64_t col_blk_size, \
                                 layout blk_layout, \
                                 index_base index, \
                                 sycl::buffer<IntType, 1> &bsr_row_ptr, \
                                 sycl::buffer<IntType, 1> &bsr_col_ind, \
                                 sycl::buffer<FpType, 1> &bsr_values); \
    DLL_EXPORT sycl::event set_bsr_data(sycl::queue &queue, \
                                        matrix_handle_t spmat, \
                                        const std::int64_t blk_nrows, \
                                        const std::int64_t blk_ncols, \
                                        const std::int64_t blk_nnz, \
                                        const std::int64_t row_blk_size, \
                                        const std::int64_t col_blk_size, \
                                        layout blk_layout, \
                                        index_base index, \
                                        IntType *bsr_row_ptr, \
                                        IntType *bsr_col_ind, \
                                        FpType *bsr_values, \
                                        const std::vector<sycl::event> &dependencies = {})

ONEMKL_DECLARE_SPARSE_SET_BSR_DATA(std::int32_t, float);
ONEMKL_DECLARE_SPARSE_SET_BSR_DATA(std::int32_t, double);
ONEMKL_DECLARE_SPARSE_SET_BSR_DATA(std::int32_t, std::complex<float>);
ONEMKL_DECLARE_SPARSE_SET_BSR_DATA(std::int32_t, std::complex<double>);
ONEMKL_DECLARE_SPARSE_SET_BSR_DATA(std::int64_t, float);
ONEMKL_DECLARE_SPARSE_SET_BSR_DATA(std::int64_t, double);
ONEMKL_DECLARE_SPARSE_SET_BSR_DATA(std::int64_t, std::complex<float>);
ONEMKL_DECLARE_SPARSE_SET_BSR_DATA(std::int64_t, std::complex<double>);

#undef ONEMKL_DECLARE_SPARSE_SET_BSR_DATA

/******************************************************************************/
//
// Types, Objects and APIs for Sparse Matrix * Sparse Matrix (matmat) multiplication
//

//
// Different VIEWS of matrix data (which may be different from the data itself)
// Views are different from the `enum class property` which describes the fixed
// property of data supplied to the matrix handle.
//
enum class matrix_view_descr : std::int32_t { general = 1 };

enum class matmat_request : std::int32_t {
    get_work_estimation_buf_size = 1,
    work_estimation = 2,

    get_compute_structure_buf_size = 3,
    compute_structure = 4,
    finalize_structure = 5,

    get_compute_buf_size = 6,
    compute = 7,
    get_nnz = 8,
    finalize = 9,
};

struct matmat_descr;
typedef matmat_descr *matmat_descr_t;

DLL_EXPORT void init_matmat_descr(matmat_descr_t *p_desc);
DLL_EXPORT void release_matmat_descr(matmat_descr_t *p_desc);

/******************************************************************************/
//
// Types, Objects and APIs for out-of-place Sparse Matrix to Sparse Matrix
// conversion (omatconvert)
//
enum class omatconvert_alg : std::int32_t {
    default_alg = 0,
};

struct omatconvert_descr;
typedef omatconvert_descr *omatconvert_descr_t;


DLL_EXPORT void init_omatconvert_descr(sycl::queue &queue, omatconvert_descr_t *p_descr);
DLL_EXPORT sycl::event release_omatconvert_descr(sycl::queue &queue, omatconvert_descr_t descr, const std::vector<sycl::event> &dependencies = {});

/******************************************************************************/
//
// Types, Objects and APIs for Sparse Matrix + Sparse Matrix (omatadd) addition
//
enum class omatadd_alg : std::int32_t {
    default_alg = 0,
};

struct omatadd_descr;
typedef omatadd_descr *omatadd_descr_t;

DLL_EXPORT void init_omatadd_descr(sycl::queue &queue,
                                   omatadd_descr_t *p_omatadd_desc);

DLL_EXPORT sycl::event release_omatadd_descr(sycl::queue &queue,
                                             omatadd_descr_t omatadd_desc,
                                             const std::vector<sycl::event> &dependencies = {});

} /* namespace oneapi::mkl::sparse */
} /* namespace mkl */
} // namespace oneapi

#endif // #ifndef _ONEMKL_SPARSE_STRUCTURES_HPP_
