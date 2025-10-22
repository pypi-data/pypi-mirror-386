#include <Python.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include "module_scanner.h"

/* ========== SIMILARITY MATCHING ========== */

static int levenshtein_distance(const char *s1, const char *s2) {
    int len1 = strlen(s1);
    int len2 = strlen(s2);

    int *d = (int *)malloc((len1 + 1) * (len2 + 1) * sizeof(int));

    for (int i = 0; i <= len1; i++) {
        d[i * (len2 + 1)] = i;
    }
    for (int j = 0; j <= len2; j++) {
        d[j] = j;
    }

    for (int i = 1; i <= len1; i++) {
        for (int j = 1; j <= len2; j++) {
            int cost = (s1[i - 1] == s2[j - 1]) ? 0 : 1;
            int del = d[(i - 1) * (len2 + 1) + j] + 1;
            int ins = d[i * (len2 + 1) + j - 1] + 1;
            int sub = d[(i - 1) * (len2 + 1) + j - 1] + cost;

            int min = del < ins ? del : ins;
            min = min < sub ? min : sub;
            d[i * (len2 + 1) + j] = min;
        }
    }

    int result = d[len1 * (len2 + 1) + len2];
    free(d);
    return result;
}

static char* normalize_name(const char *name) {
    int len = strlen(name);
    char *normalized = (char *)malloc(len * 2 + 1);
    int idx = 0;

    for (int i = 0; i < len; i++) {
        if (isupper(name[i]) && i > 0) {
            normalized[idx++] = '_';
            normalized[idx++] = tolower(name[i]);
        } else {
            normalized[idx++] = tolower(name[i]);
        }
    }
    normalized[idx] = '\0';
    return normalized;
}

static double calculate_similarity(const char *query, const char *func_name) {
    char *normalized_query = normalize_name(query);
    char *normalized_func = normalize_name(func_name);

    int distance = levenshtein_distance(normalized_query, normalized_func);
    int max_len = strlen(normalized_query) > strlen(normalized_func) ?
                  strlen(normalized_query) : strlen(normalized_func);

    double similarity = 1.0 - ((double)distance / max_len);

    free(normalized_query);
    free(normalized_func);

    return similarity > 0.0 ? similarity : 0.0;
}

static int has_substring_match(const char *query, const char *func_name) {
    char *normalized_query = normalize_name(query);
    char *normalized_func = normalize_name(func_name);

    int result = strstr(normalized_func, normalized_query) != NULL ? 1 : 0;

    free(normalized_query);
    free(normalized_func);

    return result;
}

typedef struct {
    const char *query;
    double threshold;
} SimilarityContext;

static int similarity_processor(const char *module_name,
                               const char *function_name,
                               PyObject *result_list,
                               void *user_data) {
    SimilarityContext *ctx = (SimilarityContext *)user_data;

    double similarity = calculate_similarity(ctx->query, function_name);
    if (has_substring_match(ctx->query, function_name)) {
        similarity = (similarity + 1.0) / 2.0;
    }

    if (similarity >= ctx->threshold) {
        PyObject *dict_item = create_match_dict(module_name, function_name, similarity);
        if (dict_item) {
            PyList_Append(result_list, dict_item);
            Py_DECREF(dict_item);
        }
    }

    return 0;
}

static PyObject* find_similar(PyObject* self, PyObject* args) {
    const char *keyword;
    double threshold = 0.5;

    if (!PyArg_ParseTuple(args, "s|d", &keyword, &threshold)) {
        return NULL;
    }

    PyObject* result_list = PyList_New(0);

    SimilarityContext ctx;
    ctx.query = keyword;
    ctx.threshold = threshold;

    // Direct module scanning to pass context properly
    PyObject *modules_dict = PyImport_GetModuleDict();
    Py_ssize_t pos = 0;
    PyObject *key, *value;

    while (PyDict_Next(modules_dict, &pos, &key, &value)) {
        PyObject *dir_result = PyObject_Dir(value);
        if (dir_result == NULL) {
            PyErr_Clear();
            continue;
        }

        Py_ssize_t len = PyList_Size(dir_result);
        for (Py_ssize_t i = 0; i < len; i++) {
            PyObject *item = PyList_GetItem(dir_result, i);
            const char *function_name = PyUnicode_AsUTF8(item);

            if (function_name == NULL) {
                PyErr_Clear();
                continue;
            }

            const char *module_name = PyModule_GetName(value);
            if (module_name == NULL) continue;

            // Call processor with context
            similarity_processor(module_name, function_name, result_list, (void *)&ctx);
        }
        Py_DECREF(dir_result);
    }

    return result_list;
}

/* ========== MODULE DEFINITION ========== */

static PyMethodDef module_methods[] = {
    {"find_similar", find_similar, METH_VARARGS, "Find similar functions in Python stdlib using semantic similarity. Optional threshold parameter (0.0-1.0, default 0.5)."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module_definition = {
    PyModuleDef_HEAD_INIT,
    "pylibfinder",
    "Find functions in Python stdlib by semantic similarity",
    -1,
    module_methods
};

PyMODINIT_FUNC PyInit_pylibfinder(void) {
    return PyModule_Create(&module_definition);
}
