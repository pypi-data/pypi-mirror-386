#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include <string.h>

/* ---------- your C code (sl_*, lr, lrr) ---------- */

typedef struct {
    char **items;
    size_t count;
} StringList;

static void sl_init(StringList *sl) { sl->items = NULL; sl->count = 0; }

static void sl_free(StringList *sl) {
    if (!sl) return;
    for (size_t i = 0; i < sl->count; ++i) free(sl->items[i]);
    free(sl->items);
    sl->items = NULL; sl->count = 0;
}

static void sl_add_slice(StringList *sl, const char *p, size_t len) {
    char *cpy = (char*)malloc(len + 1);
    if (!cpy) return;
    memcpy(cpy, p, len);
    cpy[len] = '\0';
    sl->items = (char**)realloc(sl->items, (sl->count + 1) * sizeof(char*));
    if (!sl->items) { free(cpy); sl->count = 0; return; }
    sl->items[sl->count++] = cpy;
}

static void sl_add_cstr(StringList *sl, const char *s) {
    sl_add_slice(sl, s, strlen(s));
}

StringList lr(const char *s, const char *left, const char *right) {
    StringList out; sl_init(&out);
    if (!s || !left || !right) return out;

    size_t n  = strlen(s);
    size_t nl = strlen(left);
    size_t nr = strlen(right);

    if (nl == 0 && nr == 0) { sl_add_cstr(&out, s); return out; }

    const char *pL = (nl == 0) ? s : strstr(s, left);
    if (!pL) return out;
    const char *start = pL + nl;

    const char *pR = (nr == 0) ? (s + n) : strstr(start, right);
    if (!pR) return out;

    sl_add_slice(&out, start, (size_t)(pR - start));
    return out;
}

StringList lrr(const char *s, const char *left, const char *right) {
    StringList out; sl_init(&out);
    if (!s || !left || !right) return out;

    size_t n  = strlen(s);
    size_t nl = strlen(left);
    size_t nr = strlen(right);

    if (nl == 0 && nr == 0) { sl_add_cstr(&out, s); return out; }

    const char *pos = s;
    while (pos < s + n) {
        const char *pL = (nl == 0) ? pos : strstr(pos, left);
        if (!pL) break;
        const char *start = pL + nl;

        const char *pR = (nr == 0) ? (s + n) : strstr(start, right);
        if (!pR) break;

        sl_add_slice(&out, start, (size_t)(pR - start));

        if (nr == 0) break;
        pos = pR + nr;
    }
    return out;
}

/* ---------- Python wrappers ---------- */

static PyObject* py_lr(PyObject* self, PyObject* args) {
    PyObject *o_s, *o_l, *o_r;
    if (!PyArg_ParseTuple(args, "UUU", &o_s, &o_l, &o_r))
        return NULL;

    const char *s    = PyUnicode_AsUTF8(o_s);
    const char *left = PyUnicode_AsUTF8(o_l);
    const char *right= PyUnicode_AsUTF8(o_r);

    StringList res = lr(s, left, right);
    PyObject *out = PyList_New((Py_ssize_t)res.count);
    if (!out) { sl_free(&res); return NULL; }

    for (size_t i = 0; i < res.count; ++i) {
        PyObject *item = PyUnicode_DecodeUTF8(res.items[i], (Py_ssize_t)strlen(res.items[i]), "strict");
        if (!item) { sl_free(&res); Py_DECREF(out); return NULL; }
        PyList_SET_ITEM(out, (Py_ssize_t)i, item); // steals ref
    }
    sl_free(&res);
    return out;
}

static PyObject* py_lrr(PyObject* self, PyObject* args) {
    PyObject *o_s, *o_l, *o_r;
    if (!PyArg_ParseTuple(args, "UUU", &o_s, &o_l, &o_r))
        return NULL;

    const char *s    = PyUnicode_AsUTF8(o_s);
    const char *left = PyUnicode_AsUTF8(o_l);
    const char *right= PyUnicode_AsUTF8(o_r);

    StringList res = lrr(s, left, right);
    PyObject *out = PyList_New((Py_ssize_t)res.count);
    if (!out) { sl_free(&res); return NULL; }

    for (size_t i = 0; i < res.count; ++i) {
        PyObject *item = PyUnicode_DecodeUTF8(res.items[i], (Py_ssize_t)strlen(res.items[i]), "strict");
        if (!item) { sl_free(&res); Py_DECREF(out); return NULL; }
        PyList_SET_ITEM(out, (Py_ssize_t)i, item);
    }
    sl_free(&res);
    return out;
}

static PyMethodDef LRMethods[] = {
    {"lr",  py_lr,  METH_VARARGS, "Return the first substring between left and right as a list (0 or 1 item)."},
    {"lrr", py_lrr, METH_VARARGS, "Return all substrings between left and right."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "_lrparse",               /* must match the module name below */
    "Left/right substring parser (C).",
    -1,
    LRMethods
};

PyMODINIT_FUNC PyInit__lrparse(void) {
    return PyModule_Create(&moduledef);
}
