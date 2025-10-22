#include <string.h>
#include "secret.h"


PyObject* verify_password_against(PyObject* self, PyObject* args) {
    PyTypeObject* cls = get_cls(self);
    if (cls == NULL) {
        return NULL;
    }

    PyObject* other;
    if (!PyArg_ParseTuple(args, "O!:verify_password_against", cls, &other)) {
        return NULL;
    }

    Py_DECREF(cls);

    SecretRef* self_secret = unlock_secret(self);

    if (self_secret == NULL) {
        return NULL;
    }

    SecretRef* other_secret = unlock_secret(other);

    if (other_secret == NULL) {
        lock_secret(self_secret);
        return NULL;
    }

    PyThreadState* _save = NULL;

    if (self_secret->bytes_len >= 2000) {
        Py_UNBLOCK_THREADS;
    }

    const int verify_result = crypto_pwhash_str_verify(
        other_secret->data,
        self_secret->data,
        (unsigned long long)self_secret->bytes_len
    );

    if (self_secret->bytes_len >= 2000) {
        Py_BLOCK_THREADS;
    }

    lock_secret(self_secret);
    lock_secret(other_secret);

    return PyBool_FromLong(!verify_result);
}

PyObject* hash(PyObject* self, PyObject* Py_UNUSED(args)) {
    SecretRef* secret = unlock_secret(self);
    if (secret == NULL) {
        return NULL;
    }

    PyTypeObject* cls = Py_TYPE(self);

    PyThreadState* _save = NULL;
    if (secret->bytes_len >= 2000) {
        Py_UNBLOCK_THREADS;
    }

    char out[crypto_pwhash_STRBYTES] = {};

    unsigned long long len = (unsigned long long)secret->bytes_len;
    int hash_result = crypto_pwhash_str(
        (char*)&out,
        secret->data,
        len,
        crypto_pwhash_OPSLIMIT_INTERACTIVE,
        crypto_pwhash_MEMLIMIT_INTERACTIVE
    );

    if (secret->bytes_len >= 2000) {
        Py_BLOCK_THREADS;
    }

    // We no longer need the secret
    lock_secret(secret);

    if (hash_result) {
        PyErr_SetString(PyExc_RuntimeError, "Could not hash password.");
        return NULL;
    }

    Py_ssize_t out_len = (Py_ssize_t)strlen(out);
    PyObject* hashed = prepare_new_secret(cls, out, out_len);

    sodium_memzero(out, crypto_pwhash_STRBYTES);

    return hashed;
}

PyObject* need_rehash(PyObject* self, PyObject* Py_UNUSED(arg)) {
    SecretRef* secret = unlock_secret(self);

    if (secret == NULL) {
        return NULL;
    }

    int check_result = crypto_pwhash_str_needs_rehash(
        secret->data,
        crypto_pwhash_OPSLIMIT_INTERACTIVE,
        crypto_pwhash_MEMLIMIT_INTERACTIVE
    );

    lock_secret(secret);

    return PyBool_FromLong(check_result);
}

PyObject* check_quality(PyObject* self, PyObject* Py_UNUSED(arg)) {
    PyTypeObject* cls = get_cls(self);

    if (cls == NULL) {
        return NULL;
    }

    SecretModuleState* state = (SecretModuleState*)PyType_GetModuleState(cls);

    Py_DECREF(cls);

    if (!state->passwdqc_configured) {
        PyErr_SetString(
            PyExc_RuntimeError,
            "passwdqc has not been configured."
        );
        return NULL;
    }

    SecretRef* secret = unlock_secret(self);

    if (secret == NULL) {
        return NULL;
    }

    const char* result = passwdqc_check(
        (const passwdqc_params_qc_t*)&state->password_checker_opts,
        secret->data,
        NULL,
        NULL
    );

    lock_secret(secret);

    if (result == NULL) {
        Py_RETURN_NONE;
    }

    Py_ssize_t len = (Py_ssize_t)strlen(result);

    return PyUnicode_DecodeUTF8(result, len, "strict");
}

PyObject* random_password(PyTypeObject* sub_cls, PyObject* Py_UNUSED(args)) {
    PyTypeObject* cls = get_cls((PyObject*)sub_cls);
    if (cls == NULL) {
        return NULL;
    }

    SecretModuleState* state = (SecretModuleState*)PyType_GetModuleState(cls);

    char* new_pass = passwdqc_random(
        (const passwdqc_params_qc_t*)&state->password_checker_opts
    );
    size_t raw_len = strlen(new_pass);
    Py_ssize_t pass_len = (Py_ssize_t)raw_len;

    PyObject* new_secret = prepare_new_secret(sub_cls, new_pass, pass_len);
    Py_DECREF(cls);

    sodium_memzero(new_pass, raw_len);
    free(new_pass);

    return new_secret;
}


PyMethodDef password_methods[] = {
    {
        .ml_name="verify_password_against",
        .ml_meth=(PyCFunction)verify_password_against,
        .ml_flags=METH_VARARGS,
        .ml_doc=PyDoc_STR(
            "Check if this password matches :code:`hashedPassword`."
        ),
    },
    {
        .ml_name="hash",
        .ml_meth=(PyCFunction)hash,
        .ml_flags=METH_NOARGS,
        .ml_doc=PyDoc_STR("Return the hash of this secret."),
    },
    {
        .ml_name="need_rehash",
        .ml_meth=(PyCFunction)need_rehash,
        .ml_flags=METH_NOARGS,
        .ml_doc=PyDoc_STR("Check if this hash need to be recreated."),
    },
    {
        .ml_name="check_quality",
        .ml_meth=(PyCFunction)check_quality,
        .ml_flags=METH_NOARGS,
        .ml_doc=PyDoc_STR("Check if the password is strong enough."),
    },
    {
        .ml_name="random_password",
        .ml_meth=(PyCFunction)random_password,
        .ml_flags=METH_NOARGS | METH_CLASS,
        .ml_doc=PyDoc_STR("Return a new random password.")
    },
    {.ml_name=NULL},
};

PyType_Slot password_type_slots[] = {
    {
        .slot=Py_tp_doc,
        .pfunc=PyDoc_STR("A password stored safely in memory."),
    },
    {
        .slot=Py_tp_methods,
        .pfunc=password_methods,
    },
    {0, 0}
};

PyType_Spec PasswordSpec = {
    .name="omniblack.secret.Password",
    .basicsize=0,
    .flags=Py_TPFLAGS_IMMUTABLETYPE | Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .slots=password_type_slots,
};
