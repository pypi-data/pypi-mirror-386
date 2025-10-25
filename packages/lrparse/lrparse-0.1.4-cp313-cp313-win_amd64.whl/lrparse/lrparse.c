#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include <string.h>

/* ---------- Dynamic string list ---------- */

typedef struct {
    char   **items;
    size_t  *lens;
    size_t   count;
} StringList;

static void sl_init(StringList *sl) {
    sl->items = NULL;
    sl->lens = NULL;
    sl->count = 0;
}

static void sl_free(StringList *sl) {
    if (!sl) return;
    for (size_t i = 0; i < sl->count; ++i)
        free(sl->items[i]);
    free(sl->items);
    free(sl->lens);
    sl->items = NULL;
    sl->lens = NULL;
    sl->count = 0;
}

static void sl_add_slice(StringList *sl, const char *p, size_t len) {
    char *cpy = malloc(len + 1);
    if (!cpy) return;

    memcpy(cpy, p, len);
    cpy[len] = '\0';

    sl->items = realloc(sl->items, (sl->count + 1) * sizeof(char*));
    sl->lens  = realloc(sl->lens,  (sl->count + 1) * sizeof(size_t));
    if (!sl->items || !sl->lens) {
        free(cpy);
        return;
    }

    sl->items[sl->count] = cpy;
    sl->lens[sl->count]  = len;
    sl->count++;
}

static const char *memmem_custom(const char *haystack, size_t hlen,
                                 const char *needle, size_t nlen) {
    if (nlen == 0) return haystack;
    if (hlen < nlen) return NULL;

    for (size_t i = 0; i <= hlen - nlen; i++)
        if (memcmp(haystack + i, needle, nlen) == 0)
            return haystack + i;
    return NULL;
}


static StringList lr(const char *s, size_t slen,
                     const char *left, size_t llen,
                     const char *right, size_t rlen)
{
    StringList out; sl_init(&out);
    size_t depth = 0;
    size_t start = 0;
    int started = 0;

    for (size_t i = 0; i + llen <= slen; i++) {

        if (memcmp(s + i, left, llen) == 0) {
            if (depth == 0) start = i + llen;
            depth++;
            i += llen - 1;
            started = 1;
            continue;
        }

        if (started && depth > 0 && memcmp(s + i, right, rlen) == 0) {
            depth--;
            if (depth == 0) {
                sl_add_slice(&out, s + start, (i - start));
                return out;
            }
            i += rlen - 1;
        }
    }

    return out;
}


static StringList lrr(const char *s, size_t slen,
                      const char *left, size_t llen,
                      const char *right, size_t rlen)
{
    StringList out; sl_init(&out);
    size_t depth = 0;
    size_t start = 0;
    int started = 0;

    for (size_t i = 0; i + llen <= slen; i++) {

        if (memcmp(s + i, left, llen) == 0) {
            if (depth == 0) start = i + llen;
            depth++;
            i += llen - 1;
            started = 1;
            continue;
        }

        if (started && depth > 0 && memcmp(s + i, right, rlen) == 0) {
            depth--;
            if (depth == 0) {
                sl_add_slice(&out, s + start, (i - start));
                started = 0;
            }
            i += rlen - 1;
        }
    }

    return out;
}


/* ---------- Python Wrappers ---------- */

static PyObject* py_lr(PyObject* self, PyObject* args) {
    PyObject *o_s, *o_l, *o_r;
    if (!PyArg_ParseTuple(args, "UUU", &o_s, &o_l, &o_r))
        return NULL;

    Py_ssize_t slen, llen, rlen;
    const char *s    = PyUnicode_AsUTF8AndSize(o_s, &slen);
    const char *left = PyUnicode_AsUTF8AndSize(o_l, &llen);
    const char *right= PyUnicode_AsUTF8AndSize(o_r, &rlen);

    StringList res = lr(s, slen, left, llen, right, rlen);

    PyObject *out = PyList_New((Py_ssize_t)res.count);
    for (size_t i = 0; i < res.count; ++i)
        PyList_SET_ITEM(out, (Py_ssize_t)i, PyUnicode_FromStringAndSize(res.items[i], res.lens[i]));

    sl_free(&res);
    return out;
}

static PyObject* py_lrr(PyObject* self, PyObject* args) {
    PyObject *o_s, *o_l, *o_r;
    if (!PyArg_ParseTuple(args, "UUU", &o_s, &o_l, &o_r))
        return NULL;

    Py_ssize_t slen, llen, rlen;
    const char *s    = PyUnicode_AsUTF8AndSize(o_s, &slen);
    const char *left = PyUnicode_AsUTF8AndSize(o_l, &llen);
    const char *right= PyUnicode_AsUTF8AndSize(o_r, &rlen);

    StringList res = lrr(s, slen, left, llen, right, rlen);

    PyObject *out = PyList_New((Py_ssize_t)res.count);
    for (size_t i = 0; i < res.count; ++i)
        PyList_SET_ITEM(out, (Py_ssize_t)i, PyUnicode_FromStringAndSize(res.items[i], res.lens[i]));

    sl_free(&res);
    return out;
}

/* ---------- Module Definition ---------- */

static PyMethodDef LRMethods[] = {
    {"lr",  py_lr,  METH_VARARGS, "Return the first substring between left and right."},
    {"lrr", py_lrr, METH_VARARGS, "Return all substrings between left and right."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "_lrparse",
    "Left/right substring parser (C).",
    -1,
    LRMethods
};

PyMODINIT_FUNC PyInit__lrparse(void) {
    return PyModule_Create(&moduledef);
}
