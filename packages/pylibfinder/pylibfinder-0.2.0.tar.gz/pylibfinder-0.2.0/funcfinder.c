#include <Python.h>
#include <regex.h>

typedef struct {
    const char* module_name;
    const char* function_name;
} FunctionInfo;

static PyObject* get_module(PyObject* self, PyObject* args) {
    const char* keyword;
    PyObject* module = NULL;
    PyObject* function = NULL;
    PyObject* module_list = PyList_New(0);

    // Parse the keyword from the arguments
    if (!PyArg_ParseTuple(args, "s", &keyword)) {
        return NULL;
    }

    // Regular expression pattern to match the keyword
    const char* pattern = keyword;

    // Compile the regular expression pattern
    regex_t regex;
    int ret = regcomp(&regex, pattern, REG_EXTENDED | REG_NOSUB);
    if (ret != 0) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to compile regular expression");
        return NULL;
    }
    // validation of function name

    // Iterate through all loaded modules
    PyObject* modules_dict = PyImport_GetModuleDict();
    Py_ssize_t pos = 0;
    PyObject* key, * value;
    while (PyDict_Next(modules_dict, &pos, &key, &value)) {
        // Check if the module has functions matching the keyword
        PyObject* dir_result = PyObject_Dir(value);
        Py_ssize_t len = PyList_Size(dir_result);
        for (Py_ssize_t i = 0; i < len; i++) {
            PyObject* item = PyList_GetItem(dir_result, i);
            const char* function_name = PyUnicode_AsUTF8(item);

            // Match the function name against the regular expression
            ret = regexec(&regex, function_name, 0, NULL, 0);
            if (ret == 0) {
                // Function found, store the module and function names
                FunctionInfo* info = (FunctionInfo*)malloc(sizeof(FunctionInfo));
                info->module_name = PyModule_GetName(value);
                info->function_name = function_name;
                PyList_Append(module_list, PyCapsule_New(info, NULL, NULL));
            }
        }
        Py_DECREF(dir_result);
    }

    // Clean up the regular expression
    regfree(&regex);

    Py_ssize_t module_count = PyList_Size(module_list);
    PyObject* result_list = PyList_New(0);  // List to store dictionaries

    for (Py_ssize_t i = 0; i < module_count; i++) {
        PyObject* capsule = PyList_GetItem(module_list, i);
        FunctionInfo* info = (FunctionInfo*)PyCapsule_GetPointer(capsule, NULL);

        PyObject* module_name = PyUnicode_FromString(info->module_name);  // Convert module name to Python object
        PyObject* function_name = PyUnicode_FromString(info->function_name);  // Convert function name to Python object

        // Create a dictionary for the module and function pair
        PyObject* dict_item = PyDict_New();
        PyDict_SetItemString(dict_item, "Module", module_name);
        PyDict_SetItemString(dict_item, "Function", function_name);

        // Append the dictionary to the result list
        PyList_Append(result_list, dict_item);

        free(info);
    }

    // Clean up and return
    Py_XDECREF(module_list);
    return result_list;


}

static PyMethodDef module_methods[] = {
    {"get_module", get_module, METH_VARARGS, "Get the modules with functions matching the keyword."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module_definition = {
    PyModuleDef_HEAD_INIT,
    "spotter",
    "A lib to spot where the keyword is defined as a function inside cpython libs and extension modules",
    -1,
    module_methods
};

PyMODINIT_FUNC PyInit_funcfinder(void) {
    return PyModule_Create(&module_definition);
}
