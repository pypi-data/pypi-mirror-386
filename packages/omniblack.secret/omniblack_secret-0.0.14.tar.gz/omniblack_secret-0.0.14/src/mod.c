#include "secret.h"

PyObject* configure_password_checker(
    PyObject* mod,
    PyObject* path
) {
    SecretModuleState* state = PyModule_GetState(mod);

    if (state == NULL) {
        return NULL;
    }

    PyObject* converted_path = PyOS_FSPath(path);

    if (converted_path == NULL) {
        return NULL;
    }

    const char* path_buffer = PyUnicode_AsUTF8AndSize(converted_path, NULL);

    if (path_buffer == NULL) {
        return NULL;
    }

    char* fail_reason;
    int password_checker_load = passwdqc_params_load(
        &state->password_checker_opts,
        &fail_reason,
        path_buffer
    );

    if (password_checker_load) {
        passwdqc_params_reset(&state->password_checker_opts);
        state->passwdqc_configured = false;
        PyErr_SetString(PyExc_RuntimeError, fail_reason);
        return NULL;
    } else {
        state->passwdqc_configured = true;
    }

    Py_RETURN_TRUE;
}

PyObject* is_password_checker_configured(
    PyObject* mod,
    PyObject* Py_UNUSED(args)
) {
    SecretModuleState* state = PyModule_GetState(mod);

    if (state == NULL) {
        return NULL;
    }

    return PyBool_FromLong(state->passwdqc_configured);
}

void m_free(PyObject* mod) {
    SecretModuleState* state = PyModule_GetState(mod);
    if (state == NULL) {
        return;
    }

    if (state->passwdqc_configured) {
        passwdqc_params_free(&state->password_checker_opts);
    }
}

int m_clear(PyObject* mod) {
    SecretModuleState* state = PyModule_GetState(mod);
    if (state == NULL) {
        return -1;
    }

    Py_CLEAR(state->Password);
    Py_CLEAR(state->Secret);
    return 0;
}

int m_traverse(PyObject* mod, visitproc visit, void* arg) {
    SecretModuleState* state = PyModule_GetState(mod);
    if (state == NULL) {
        return -1;
    }

    Py_VISIT(state->Password);
    Py_VISIT(state->Secret);
    return 0;
}

int exec_module(PyObject* mod) {
    if (sodium_init() < 0) {
        PyErr_SetString(PyExc_RuntimeError, "Could not load libsodium.");
        return -1;
    }

    PyTypeObject* secret_type = (PyTypeObject*)PyType_FromModuleAndSpec(
        mod,
        &SecretSpec,
        NULL
    );

    if (secret_type == NULL) {
        return -1;
    }

    int secret_result = PyModule_AddType(mod, secret_type);

    if (secret_result == -1) {
        return secret_result;
    }

    PyTypeObject* password_type = (PyTypeObject*)PyType_FromModuleAndSpec(
        mod,
        &PasswordSpec,
        (PyObject*)secret_type
    );

    if (password_type == NULL) {
        return -1;
    }

    int password_result = PyModule_AddType(mod, password_type);

    if (password_result == -1) {
        return password_result;
    }


    SecretModuleState* state = PyModule_GetState(mod);

    if (state == NULL) {
        return -1;
    }

    char* fail_reason;
    int password_checker_load = passwdqc_params_load(
        &state->password_checker_opts,
        &fail_reason,
        "/etc/passwdqc.conf"
    );

    if (!password_checker_load) {
        state->passwdqc_configured = true;
    } else {
        state->passwdqc_configured = false;
        passwdqc_params_reset(&state->password_checker_opts);
    }

    state->Secret = secret_type;
    state->Password = password_type;

    return 0;
}

PyMethodDef module_methods[] = {
    {
        .ml_name="configure_password_checker",
        .ml_meth=(PyCFunction)configure_password_checker,
        .ml_flags=METH_O,
        .ml_doc=PyDoc_STR(
            "Use the configuration at \"path\" for the password checker.\n"
            "This should be a valid configuration file for libpasswdqc.\n"
            "By default we use :code:`/etc/passwdqc.conf`."
        )
    },
    {
        .ml_name="is_password_checker_configured",
        .ml_meth=(PyCFunction)is_password_checker_configured,
        .ml_flags=METH_NOARGS,
        .ml_doc=PyDoc_STR(
            "Has the libpasswdqc configuration load successfully?"
        )
    },
    {.ml_name=NULL}
};

PyModuleDef_Slot module_slots[] = {
    {.slot=Py_mod_exec, .value=exec_module},
    {0, NULL},
};

PyModuleDef secret_mod = {
    PyModuleDef_HEAD_INIT,
    .m_name="omniblack.secret",
    .m_doc=PyDoc_STR(
        "A module for handling secret data in a way to reduce leaks."
    ),
    .m_size=sizeof(SecretModuleState),
    .m_traverse=m_traverse,
    .m_clear=m_clear,
    .m_free=(freefunc)m_free,
    .m_slots=module_slots,
    .m_methods=module_methods
};

PyMODINIT_FUNC PyInit_secret(void) {
    return PyModuleDef_Init(&secret_mod);
}
