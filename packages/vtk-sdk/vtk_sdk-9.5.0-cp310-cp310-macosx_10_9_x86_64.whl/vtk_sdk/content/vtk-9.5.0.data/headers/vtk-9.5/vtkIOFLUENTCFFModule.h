
#ifndef VTKIOFLUENTCFF_EXPORT_H
#define VTKIOFLUENTCFF_EXPORT_H

#ifdef VTKIOFLUENTCFF_STATIC_DEFINE
#  define VTKIOFLUENTCFF_EXPORT
#  define VTKIOFLUENTCFF_NO_EXPORT
#else
#  ifndef VTKIOFLUENTCFF_EXPORT
#    ifdef IOFLUENTCFF_EXPORTS
        /* We are building this library */
#      define VTKIOFLUENTCFF_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define VTKIOFLUENTCFF_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef VTKIOFLUENTCFF_NO_EXPORT
#    define VTKIOFLUENTCFF_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef VTKIOFLUENTCFF_DEPRECATED
#  define VTKIOFLUENTCFF_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef VTKIOFLUENTCFF_DEPRECATED_EXPORT
#  define VTKIOFLUENTCFF_DEPRECATED_EXPORT VTKIOFLUENTCFF_EXPORT VTKIOFLUENTCFF_DEPRECATED
#endif

#ifndef VTKIOFLUENTCFF_DEPRECATED_NO_EXPORT
#  define VTKIOFLUENTCFF_DEPRECATED_NO_EXPORT VTKIOFLUENTCFF_NO_EXPORT VTKIOFLUENTCFF_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef VTKIOFLUENTCFF_NO_DEPRECATED
#    define VTKIOFLUENTCFF_NO_DEPRECATED
#  endif
#endif

/* VTK-HeaderTest-Exclude: vtkIOFLUENTCFFModule.h */

/* Include ABI Namespace */
#include "vtkABINamespace.h"

#endif /* VTKIOFLUENTCFF_EXPORT_H */
