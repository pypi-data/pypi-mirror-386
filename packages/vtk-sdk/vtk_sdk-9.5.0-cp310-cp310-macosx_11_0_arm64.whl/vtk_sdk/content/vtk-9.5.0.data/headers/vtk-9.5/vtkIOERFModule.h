
#ifndef VTKIOERF_EXPORT_H
#define VTKIOERF_EXPORT_H

#ifdef VTKIOERF_STATIC_DEFINE
#  define VTKIOERF_EXPORT
#  define VTKIOERF_NO_EXPORT
#else
#  ifndef VTKIOERF_EXPORT
#    ifdef IOERF_EXPORTS
        /* We are building this library */
#      define VTKIOERF_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define VTKIOERF_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef VTKIOERF_NO_EXPORT
#    define VTKIOERF_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef VTKIOERF_DEPRECATED
#  define VTKIOERF_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef VTKIOERF_DEPRECATED_EXPORT
#  define VTKIOERF_DEPRECATED_EXPORT VTKIOERF_EXPORT VTKIOERF_DEPRECATED
#endif

#ifndef VTKIOERF_DEPRECATED_NO_EXPORT
#  define VTKIOERF_DEPRECATED_NO_EXPORT VTKIOERF_NO_EXPORT VTKIOERF_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef VTKIOERF_NO_DEPRECATED
#    define VTKIOERF_NO_DEPRECATED
#  endif
#endif

/* VTK-HeaderTest-Exclude: vtkIOERFModule.h */

/* Include ABI Namespace */
#include "vtkABINamespace.h"

#endif /* VTKIOERF_EXPORT_H */
