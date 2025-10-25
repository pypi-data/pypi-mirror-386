#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include <string.h>

/* ---------- Dynamic list ---------- */

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
}

static void sl_add_slice(StringList *sl, const char *p, size_t len) {
    char *cpy = malloc(len + 1);
    memcpy(cpy, p, len);
    cpy[len] = '\0';

    sl->items = realloc(sl->items, (sl->count + 1) * sizeof(char *));
    sl->lens  = realloc(sl->lens,  (sl->count + 1) * sizeof(size_t));

    sl->items[sl->count] = cpy;
    sl->lens[sl->count]  = len;
    sl->count++;
}


static const char *memmem_custom(const char *h, size_t hl,
                                 const char *n, size_t nl) {
    if (nl == 0) return h;
    if (hl < nl) return NULL;
    for (size_t i = 0; i <= hl - nl; i++)
        if (memcmp(h + i, n, nl) == 0)
            return h + i;
    return NULL;
}


static StringList lr(const char *s, size_t slen,
                     const char *left, size_t llen,
                     const char *right, size_t rlen)
{
    StringList out; sl_init(&out);

    if (llen == 0 && rlen == 0) {
        sl_add_slice(&out, s, slen);
        return out;
    }

    if (llen == 0) {
        const char *pR = memmem_custom(s, slen, right, rlen);
        if (!pR) return out;
        sl_add_slice(&out, s, (size_t)(pR - s));
        return out;
    }

    if (rlen == 0) {
        const char *pL = memmem_custom(s, slen, left, llen);
        if (!pL) return out;
        const char *start = pL + llen;
        sl_add_slice(&out, start, slen - (start - s));
        return out;
    }

    int same = (llen == rlen && memcmp(left, right, llen) == 0);

    size_t depth = 0;
    size_t start = 0;
    int started = 0;

    for (size_t i = 0; i + llen <= slen; i++) {

        if (same && memcmp(s + i, left, llen) == 0) {
            if (depth == 0) {
                start = i + llen;
                depth = 1;
                started = 1;
            } else {
                sl_add_slice(&out, s + start, i - start);
                return out;
            }
            i += llen - 1;
            continue;
        }

        if (!same && memcmp(s + i, left, llen) == 0) {
            if (depth == 0) start = i + llen;
            depth++;
            started = 1;
            i += llen - 1;
            continue;
        }

        if (!same && started && depth > 0 && memcmp(s + i, right, rlen) == 0) {
            depth--;
            if (depth == 0) {
                sl_add_slice(&out, s + start, i - start);
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

    if (llen == 0 && rlen == 0) {
        sl_add_slice(&out, s, slen);
        return out;
    }

    if (llen == 0 || rlen == 0) {
        return out;
    }

    int same = (llen == rlen && memcmp(left, right, llen) == 0);
    size_t pos = 0;

    if (same) {
        while (pos + llen <= slen) {

            const char *open = memmem_custom(s + pos, slen - pos, left, llen);
            if (!open) break;
            size_t start = (size_t)(open - s) + llen;

            const char *close = memmem_custom(s + start, slen - start, right, rlen);
            if (!close) break; 

            sl_add_slice(&out, s + start, (size_t)(close - (s + start)));
            pos = (size_t)(close - s) + rlen;
        }
        return out;
    }

    while (pos + llen <= slen) {

        const char *pL = memmem_custom(s + pos, slen - pos, left, llen);
        if (!pL) break;

        size_t i = (size_t)(pL - s) + llen;
        size_t depth = 1; 

        
        while (i + rlen <= slen) {
            if (i + llen <= slen && memcmp(s + i, left, llen) == 0) {
                depth++;
                i += llen;
                continue;
            }
            if (memcmp(s + i, right, rlen) == 0) {
                depth--;
                if (depth == 0) {
                 
                    size_t from = (size_t)(pL - s) + llen;
                    sl_add_slice(&out, s + from, i - from);
                    i += rlen;
                    pos = i; 
                    goto next_block;
                }
                i += rlen;
                continue;
            }
            i++; 
        }

        break;

    next_block:
        ; 
    }

    return out;
}


/* ---------- Python Layer ---------- */

static PyObject* py_lr(PyObject* self, PyObject* args) {
    PyObject *o_s, *o_l, *o_r;
    Py_ssize_t slen, llen, rlen;
    if (!PyArg_ParseTuple(args, "UUU", &o_s, &o_l, &o_r)) return NULL;

    const char *s    = PyUnicode_AsUTF8AndSize(o_s, &slen);
    const char *left = PyUnicode_AsUTF8AndSize(o_l, &llen);
    const char *right= PyUnicode_AsUTF8AndSize(o_r, &rlen);

    StringList res = lr(s, slen, left, llen, right, rlen);
    PyObject *out = PyList_New(res.count);
    for (size_t i = 0; i < res.count; i++)
        PyList_SET_ITEM(out, i, PyUnicode_FromStringAndSize(res.items[i], res.lens[i]));
    sl_free(&res);
    return out;
}

static PyObject* py_lrr(PyObject* self, PyObject* args) {
    PyObject *o_s, *o_l, *o_r;
    Py_ssize_t slen, llen, rlen;
    if (!PyArg_ParseTuple(args, "UUU", &o_s, &o_l, &o_r)) return NULL;

    const char *s    = PyUnicode_AsUTF8AndSize(o_s, &slen);
    const char *left = PyUnicode_AsUTF8AndSize(o_l, &llen);
    const char *right= PyUnicode_AsUTF8AndSize(o_r, &rlen);

    StringList res = lrr(s, slen, left, llen, right, rlen);
    PyObject *out = PyList_New(res.count);
    for (size_t i = 0; i < res.count; i++)
        PyList_SET_ITEM(out, i, PyUnicode_FromStringAndSize(res.items[i], res.lens[i]));
    sl_free(&res);
    return out;
}

static PyMethodDef LRMethods[] = {
    {"lr",  py_lr,  METH_VARARGS, "Extract first substring"},
    {"lrr", py_lrr, METH_VARARGS, "Extract all substrings"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "_lrparse",
    "Left/right substring parser.",
    -1,
    LRMethods
};

PyMODINIT_FUNC PyInit__lrparse(void) {
    return PyModule_Create(&moduledef);
}
