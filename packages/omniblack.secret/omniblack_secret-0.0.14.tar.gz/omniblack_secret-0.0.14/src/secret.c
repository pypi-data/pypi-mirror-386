#include "secret.h"

#include <stdbool.h>
#include <string.h>

PyObject* get_cls_impl(
    PyObject *Py_UNUSED(self),
    PyTypeObject *defining_class,
    PyObject *const *Py_UNUSED(args),
    Py_ssize_t Py_UNUSED(nargs),
    PyObject *Py_UNUSED(kwnames)
) {
    PyObject* cls = (PyObject*)defining_class;
    Py_INCREF(cls);
    return cls;
}

PyTypeObject* get_cls(PyObject* self) {
    PyObject* method = PyObject_GetAttrString(self, "_get_cls");

    if (method == NULL) {
        return NULL;
    }

    PyTypeObject* cls = (PyTypeObject*)PyObject_CallNoArgs(method);
    Py_XINCREF((PyObject*)cls);

    return cls;
}

SecretRef* accessInternalStorage(PyObject* self) {
    PyTypeObject* cls = get_cls(self);

    if (cls == NULL) {
        return NULL;
    }

    SecretRef* result = PyObject_GetTypeData(self, cls);
    Py_DECREF(cls);
    return result;
}

SecretRef* unlock_secret(PyObject* self) {
    SecretRef* self_slot = accessInternalStorage(self);

    if (self_slot == NULL) {
        return NULL;
    }

    volatile int reader_num = ++self_slot->readers;

    if (reader_num == 1) {
        sodium_mprotect_readonly(self_slot->data);
    }
    return self_slot;
}

void lock_secret(SecretRef* self) {
    volatile int readers_left = --self->readers;

    if (readers_left == 0) {
        sodium_mprotect_noaccess(self->data);
    }
}

PyObject *reveal(PyObject* self, PyObject* Py_UNUSED(unsused)) {
    SecretRef* secret = unlock_secret(self);

    if (secret == NULL) {
        return NULL;
    }

    PyObject* string = PyUnicode_DecodeUTF8(
        secret->data,
        secret->bytes_len,
        "strict"
    );

    lock_secret(secret);

    if (string == NULL) {
        return NULL;
    }

    return string;
}

PyObject* rich(PyObject* self, PyObject* Py_UNUSED(arg)) {
    PyTypeObject* cls = Py_TYPE(self);
    PyObject* cls_name = PyType_GetName(cls);

    return PyUnicode_FromFormat(
        "<[red]%U Redacted[/]>",
        cls_name
    );
}

PyObject *tp_repr(PyObject* self) {
    PyTypeObject* cls = Py_TYPE(self);
    PyObject* cls_name = PyType_GetName(cls);
    return PyUnicode_FromFormat(
        "<%U Redacted>",
        cls_name
    );
}

void tp_dealloc(PyObject* self) {
    SecretRef* self_slot = accessInternalStorage(self);

    if (self_slot == NULL) {
        return;
    }

    PyObject_GC_UnTrack(self);
    sodium_free(self_slot->data);

    PyTypeObject *tp = Py_TYPE(self);
    freefunc sub_tp_free = PyType_GetSlot(tp, Py_tp_free);
    sub_tp_free(self);
    Py_DECREF(tp);
}

int tp_traverse(PyObject* self, visitproc visit, void *arg) {
    Py_VISIT(Py_TYPE(self));
    return 0;
}

int tp_clear(PyObject* Py_UNUSED(self)) {
    return 0;
}

Py_ssize_t code_points_len(const char* data, Py_ssize_t bytes_len) {
    Py_ssize_t len = 0;

    // ASCII is only 7 bits so the highest bit will never be set
    // For multibyte unicode codepoints the first byte's high bits
    // will be set to `11`, and the high bits of continuation bytes
    // will be set to `10`. Therefore (*data & 0xC0) will only be
    // 0x80 for continuation bytes, and count all bytes not starting
    // with `10` count all starting bytes and ASCII bytes
    // .. the number of bytes.
    for (int i = 0; i < bytes_len; i += 1) {
        len += (data[i] & 0xC0) != 0x80;
    }

    return len;
}

PyObject* prepare_new_secret(
    PyTypeObject* cls,
    const char* data,
    Py_ssize_t len
) {
    allocfunc tp_alloc = PyType_GetSlot(cls, Py_tp_alloc);
    PyObject* new_self = tp_alloc(cls, 0);

    size_t c_len = (size_t)len;

    if (new_self == NULL) {
        return NULL;
    }

    SecretRef* new_self_slot = accessInternalStorage(new_self);

    if (new_self_slot == NULL) {
        Py_DECREF(new_self);
        return NULL;
    }

    char* secret_buffer = sodium_malloc(c_len + 1);

    if (secret_buffer == NULL) {
        Py_DECREF(new_self);
        return PyErr_SetFromErrno(PyExc_MemoryError);
    }

    // Copy our secret into the new buffer
    memcpy(secret_buffer, data, c_len);

    // Add null terminator for api's that expect
    // a null terminated string.
    secret_buffer[c_len] = 0;

    // Copy the metadata into the new python object
    new_self_slot->bytes_len = len;
    new_self_slot->data = secret_buffer;

    // We are the reader. Setting it one means lock_secret will
    // correctly Re-protect the memory.
    new_self_slot->readers = 1;

    // Re-protect the new and old secret
    lock_secret(new_self_slot);

    return new_self;
}


PyObject* tp_new(PyTypeObject *subtype, PyObject *args, PyObject *kwds) {
    // Parse the args we were passed
    static char* names[] = {"", NULL};
    PyObject* object; // Borrowed reference
    bool parse_result = PyArg_ParseTupleAndKeywords(
        args,
        kwds,
        "O:Secret",
        names,
        &object
    );

    if (!parse_result) {
        return NULL;
    }

    // Coerce our argument to a python `str`
    // this is the same as calling `str` in object
    PyObject* string = PyObject_Str(object);
    if (string == NULL) {
        return NULL;
    }

    // Get the underlying character data in utf-8
    // this data shares the lifetime of `string`
    // NOTE: we can't zero this memory as it is controlled by python
    Py_ssize_t len;
    const char* data_buffer = PyUnicode_AsUTF8AndSize(string, &len);

    if (data_buffer == NULL) {
        Py_DECREF(string);
        return NULL;
    }

    size_t c_len = (size_t)len;

    char* secret_buffer = sodium_malloc(c_len);
    memcpy(secret_buffer, data_buffer, c_len);

    PyObject* self = prepare_new_secret(subtype, secret_buffer, len);
    Py_DECREF(string);

    return self;
}

PyObject* copy(PyObject* self, PyObject* Py_UNUSED(arg)) {
    PyTypeObject* subtype = Py_TYPE(self);
    // Get the data to copy
    SecretRef* old_secret = unlock_secret(self);

    PyObject* new_self = prepare_new_secret(
        subtype,
        old_secret->data,
        old_secret->bytes_len
    );

    lock_secret(old_secret);
    return new_self;
}

Py_ssize_t sq_length(PyObject* self) {
    SecretRef* secret = unlock_secret(self);

    if (secret == NULL) {
        return -1;
    }

    Py_ssize_t len = code_points_len(secret->data, secret->bytes_len);
    lock_secret(secret);
    return len;
}

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wincompatible-pointer-types"
PyMethodDef methods[] = {
    {
        .ml_name="__copy__",
        .ml_meth=(PyCFunction)copy,
        .ml_flags=METH_NOARGS,
        .ml_doc=PyDoc_STR("Return a copy of the secret."),
    },
    {
        .ml_name="__deepcopy__",
        .ml_meth=(PyCFunction)copy,
        .ml_flags=METH_O,
        .ml_doc=PyDoc_STR("Return a copy of the secret."),
    },
    {
        .ml_name="__rich__",
        .ml_meth=(PyCFunction)rich,
        .ml_flags=METH_NOARGS,
        .ml_doc=PyDoc_STR("Return a string `rich` can pretty print.")
    },
    {
        .ml_name="reveal",
        .ml_meth=(PyCFunction)reveal,
        .ml_flags=METH_NOARGS,
        .ml_doc=PyDoc_STR("Return the secret in the form of a string.")
    },
    {
        .ml_name="random_secret",
        .ml_meth=(PyCFunction)random_secret,
        .ml_flags=METH_VARARGS | METH_CLASS,
        .ml_doc=PyDoc_STR("Return a new random url safe string."),
    },
    {
        .ml_name="_get_cls",
        .ml_meth=(PyCMethod)get_cls_impl,
        .ml_flags=METH_METHOD | METH_FASTCALL | METH_KEYWORDS | METH_CLASS,
        .ml_doc=PyDoc_STR("Return the secret classes associated with self.")
    },
    {.ml_name=NULL},
};
#pragma GCC diagnostic pop

PyType_Slot type_slots[] = {
    {
        .slot=Py_tp_doc,
        .pfunc=PyDoc_STR("A secret stored safely in memory."),
    },
    {
        .slot=Py_tp_repr,
        .pfunc=tp_repr,
    },
    {
        .slot=Py_tp_new,
        .pfunc=tp_new,
    },
    {
        .slot=Py_tp_methods,
        .pfunc=methods,
    },
    {
        .slot=Py_tp_dealloc,
        .pfunc=tp_dealloc,
    },
    {
        .slot=Py_tp_traverse,
        .pfunc=tp_traverse,
    },
    {
        .slot=Py_tp_clear,
        .pfunc=tp_clear,
    },
    {
        .slot=Py_sq_length,
        .pfunc=sq_length,
    },
    {0, 0}
};

PyType_Spec SecretSpec = {
    .name="omniblack.secret.Secret",
    .basicsize=-(Py_ssize_t)sizeof(SecretRef),
    .flags=(
        Py_TPFLAGS_IMMUTABLETYPE
        | Py_TPFLAGS_DEFAULT
        | Py_TPFLAGS_HAVE_GC
        | Py_TPFLAGS_BASETYPE
    ),
    .slots=type_slots,
};
