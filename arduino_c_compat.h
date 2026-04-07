#ifndef ARDUINO_C_COMPAT_H
#define ARDUINO_C_COMPAT_H

static inline int cstr_equals(const char* left, const char* right) {
  if (left == 0 || right == 0) {
    return 0;
  }

  while (*left != '\0' && *right != '\0') {
    if (*left != *right) {
      return 0;
    }
    ++left;
    ++right;
  }

  return *left == '\0' && *right == '\0';
}

#endif
