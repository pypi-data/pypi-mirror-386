/*
    Copyright Intel Corporation.
    
    This software and the related documents are Intel copyrighted materials, and
    your use of them is governed by the express license under which they were
    provided to you (License). Unless the License provides otherwise, you may
    not use, modify, copy, publish, distribute, disclose or transmit this
    software or the related documents without Intel's prior written permission.
    
    This software and the related documents are provided as is, with no express
    or implied warranties, other than those that are expressly stated in the
    License.
*/
#pragma once

#define CCL_FORCEINLINE   inline __attribute__((always_inline))
#define CCL_FORCENOINLINE __attribute__((noinline))

#if (__GNUC__ >= 6) || defined(__clang__)
#   define CCL_DEPRECATED_ENUM_FIELD __attribute__((deprecated))
#else
#   define CCL_DEPRECATED_ENUM_FIELD
#endif

#if defined(__GNUC__)
#   define CCL_DEPRECATED __attribute__((deprecated))
#else
#   define CCL_DEPRECATED
#endif

/* All symbols shall be internal unless marked as CCL_API */
#ifdef __linux__
#   if __GNUC__ >= 4
#       define CCL_HELPER_DLL_EXPORT __attribute__ ((visibility ("default")))
#   else
#       define CCL_HELPER_DLL_EXPORT
#   endif
#else
#error "unexpected OS"
#endif

#define CCL_API CCL_HELPER_DLL_EXPORT

#define ONECCL_SPEC_VERSION "1.0"

#define CCL_MAJOR_VERSION           2021
#define CCL_MINOR_VERSION           17
#define CCL_UPDATE_VERSION          0
#define CCL_PRODUCT_STATUS     "Gold"
#define CCL_PRODUCT_BUILD_DATE "2025-10-16T 09:12:32Z"
#define CCL_PRODUCT_FULL       "Gold-2021.17.0 2025-10-16T 09:12:32Z (HEAD/81a2319)"

#if defined(SYCL_LANGUAGE_VERSION) && defined (__INTEL_LLVM_COMPILER)
#define CCL_ENABLE_SYCL
#define CCL_ENABLE_ZE
#endif
