#pragma once

#define Py_LIMITED_API 0x030c0000
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <sodium.h>
#include <passwdqc.h>
#include <stdbool.h>

#define DLL_PUBLIC __attribute__ ((visibility ("default")))

extern PyModuleDef secret_mod;
extern PyType_Spec SecretSpec;
extern PyType_Spec PasswordSpec;

typedef struct {
    PyTypeObject* Secret;
    PyTypeObject* Password;
    bool passwdqc_configured;
    passwdqc_params_t password_checker_opts;
} SecretModuleState;

typedef struct {
    volatile int readers;
    Py_ssize_t bytes_len;
    char* data;
} SecretRef;

PyTypeObject* get_cls(PyObject* self);
SecretRef* unlock_secret(PyObject* self);
void lock_secret(SecretRef* self);
PyObject* random_secret(PyTypeObject* cls, PyObject* args);

PyObject* prepare_new_secret(
    PyTypeObject* cls,
    const char* data,
    Py_ssize_t len
);
