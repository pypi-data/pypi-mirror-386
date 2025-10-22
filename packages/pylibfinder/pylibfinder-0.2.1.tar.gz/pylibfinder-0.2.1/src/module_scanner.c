#include "module_scanner.h"
#include <string.h>

void scan_all_modules(function_processor processor, void *user_data) {
    PyObject *modules_dict = PyImport_GetModuleDict();

    Py_ssize_t pos = 0;
    PyObject *key, *value;

    while (PyDict_Next(modules_dict, &pos, &key, &value)) {
        PyObject *dir_result = PyObject_Dir(value);
        if (dir_result == NULL) {
            continue;
        }

        Py_ssize_t len = PyList_Size(dir_result);
        for (Py_ssize_t i = 0; i < len; i++) {
            PyObject *item = PyList_GetItem(dir_result, i);
            const char *function_name = PyUnicode_AsUTF8(item);

            if (function_name == NULL) continue;

            const char *module_name = PyModule_GetName(value);
            if (module_name == NULL) continue;

            // Call the processor callback with user_data as the result_list
            processor(module_name, function_name, (PyObject *)user_data, NULL);
        }
        Py_DECREF(dir_result);
    }
}

PyObject* create_match_dict(const char *module_name,
                           const char *function_name,
                           double score) {
    PyObject *dict_item = PyDict_New();
    if (!dict_item) return NULL;

    PyObject *mod_obj = PyUnicode_FromString(module_name);
    PyObject *func_obj = PyUnicode_FromString(function_name);
    PyObject *score_obj = PyFloat_FromDouble(score);

    if (!mod_obj || !func_obj || !score_obj) {
        Py_XDECREF(dict_item);
        Py_XDECREF(mod_obj);
        Py_XDECREF(func_obj);
        Py_XDECREF(score_obj);
        return NULL;
    }

    PyDict_SetItemString(dict_item, "Module", mod_obj);
    PyDict_SetItemString(dict_item, "Function", func_obj);
    if (score > 0) {
        PyDict_SetItemString(dict_item, "Score", score_obj);
    }

    Py_DECREF(mod_obj);
    Py_DECREF(func_obj);
    Py_DECREF(score_obj);

    return dict_item;
}
