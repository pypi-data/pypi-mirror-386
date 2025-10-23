// SPDX-FileCopyrightText: Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
// SPDX-License-Identifier: BSD-3-Clause
/**
 * When using 'scn' in VTK, this header enables use to use either the scn
 * version provided by VTK or an externally built version based on compile time
 * flags.
 *
 * When using 'scn' include this header and then include any scn header you need
 * as follows:
 *
 * ```c++
 *
 *  #include <vtk_scn.>
 *
 *  // clang-format off
 *  #include VTK_SCN(scn/scan.h)
 *  // clang-format on
 *
 * ```
 *
 * Note the clang-format sentinels are need avoid incorrect formatting the
 * VTK_SCN macro call when using clang-format to format the code.
 */

#ifndef vtk_scn_h
#define vtk_scn_h

/* Use the scn library configured for VTK.  */
#define VTK_MODULE_USE_EXTERNAL_VTK_scn 0

#if VTK_MODULE_USE_EXTERNAL_VTK_scn
# define VTK_SCN(header) <header>
#else
# define VTK_SCN(header) <vtkscn/include/vtk##header>
#endif

#endif // #ifndef vtk_scn_h
