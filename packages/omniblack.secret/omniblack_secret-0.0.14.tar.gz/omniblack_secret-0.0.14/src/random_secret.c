#include "secret.h"

static char ALPHABET[] = {
    'a',
    'b',
    'c',
    'd',
    'e',
    'f',
    'g',
    'h',
    'i',
    'j',
    'k',
    'l',
    'm',
    'n',
    'o',
    'p',
    'q',
    'r',
    's',
    't',
    'u',
    'v',
    'w',
    'x',
    'y',
    'z',

    'A',
    'B',
    'C',
    'D',
    'E',
    'F',
    'G',
    'H',
    'I',
    'J',
    'K',
    'L',
    'M',
    'N',
    'O',
    'P',
    'Q',
    'R',
    'S',
    'T',
    'U',
    'V',
    'W',
    'X',
    'Y',
    'Z',

    '0',
    '1',
    '2',
    '3',
    '4',
    '5',
    '6',
    '7',
    '8',
    '9',

    '_',
    '-',
};

PyObject* random_secret(PyTypeObject* cls, PyObject* args) {
    Py_ssize_t py_num_of_chars;

    if (!PyArg_ParseTuple(args, "n:random_secret", &py_num_of_chars)) {
        return NULL;
    }

    if (py_num_of_chars <= 0) {
        PyErr_SetString(
            PyExc_ValueError,
            (
                "omniblack.secret.Secret.random_secret"
                " accepts one positive number."
            )
        );
        return NULL;
    }

    size_t num_of_chars = (size_t)py_num_of_chars;

    size_t num_of_bytes = (num_of_chars * 8) / 6;
    uint8_t* random_buffer = sodium_malloc(num_of_bytes);

    if (random_buffer == NULL) {
        return PyErr_NoMemory();
    }

    randombytes_buf(random_buffer, num_of_bytes);

    char* new_string = sodium_malloc(num_of_chars);

    if (new_string == NULL) {
        sodium_free(random_buffer);
        return PyErr_NoMemory();
    }

    uint8_t remainder = 0;
    uint8_t remaining_width = 0;

    for (size_t i = 0; i < num_of_chars; i += 1) {
        if (remaining_width == 6) {
            new_string[i] = ALPHABET[remainder];
            remaining_width = 0;
            remainder = 0;
        } else {
            uint8_t byte = random_buffer[i];
            uint8_t new_remaining_mask = (uint8_t)(
                255 << (6 - remaining_width)
            );
            uint8_t char_mask = 255 ^ new_remaining_mask;

            uint8_t new_remaining_digits = new_remaining_mask & byte;
            new_remaining_digits >>= (6 - remaining_width);

            uint8_t char_digits = byte & char_mask;
            char_digits <<= remaining_width;
            uint8_t current_char = remainder | char_digits;

            new_string[i] = ALPHABET[current_char];

            remaining_width += 2;
            remainder = new_remaining_digits;
        }
    }

    PyObject* result = prepare_new_secret(cls, new_string, py_num_of_chars);

    sodium_free(new_string);

    return result;
}
