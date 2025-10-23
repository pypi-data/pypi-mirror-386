/*==============================================================================
 Copyright (c) 2025 Antares <antares0982@gmail.com>

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
 *============================================================================*/

#ifdef SSRJSON_CLANGD_DUMMY
#    ifndef COMPILE_CONTEXT_ENCODE
#        define COMPILE_CONTEXT_ENCODE
#    endif
#    ifndef COMPILE_INDENT_LEVEL
#        include "encode/indent_writer.h"
#        include "encode_shared.h"
#        include "simd/simd_detect.h"
#        include "simd/simd_impl.h"
#        include "utils/unicode.h"
#        define COMPILE_INDENT_LEVEL 0
#        define COMPILE_READ_UCS_LEVEL 1
#        define COMPILE_WRITE_UCS_LEVEL 1
#        include "simd/compile_feature_check.h"
#    endif
#endif

/* Macro IN */
#include "compile_context/sirw_in.inl.h"

force_inline bool unicode_buffer_append_key_internal(const _src_t *str_data, usize len, _dst_t **writer_addr, EncodeUnicodeBufferInfo *unicode_buffer_info, Py_ssize_t cur_nested_depth) {
    static_assert(COMPILE_READ_UCS_LEVEL <= COMPILE_WRITE_UCS_LEVEL, "COMPILE_READ_UCS_LEVEL <= COMPILE_WRITE_UCS_LEVEL");
    RETURN_ON_UNLIKELY_ERR(!unicode_buffer_reserve(writer_addr, unicode_buffer_info, get_indent_char_count(cur_nested_depth, COMPILE_INDENT_LEVEL) + 5 + 6 * len + TAIL_PADDING));
    _dst_t *writer = *writer_addr;
    write_unicode_indent(&writer, cur_nested_depth);
    *writer++ = '"';
    encode_unicode_impl(&writer, str_data, len, true);
    *writer++ = '"';
    *writer++ = ':';
#if COMPILE_INDENT_LEVEL > 0
    *writer++ = ' ';
#    if SIZEOF_VOID_P == 8 || COMPILE_WRITE_UCS_LEVEL != 4
    *writer = 0;
#    endif // SIZEOF_VOID_P == 8 || COMPILE_WRITE_UCS_LEVEL != 4
#endif     // COMPILE_INDENT_LEVEL > 0
    *writer_addr = writer;
    assert(check_unicode_writer_valid(writer, unicode_buffer_info));
    return true;
}

force_inline bool unicode_buffer_append_str_internal(const _src_t *str_data, usize len, _dst_t **writer_addr,
                                                     EncodeUnicodeBufferInfo *unicode_buffer_info, Py_ssize_t cur_nested_depth, bool is_in_obj) {
    static_assert(COMPILE_READ_UCS_LEVEL <= COMPILE_WRITE_UCS_LEVEL, "COMPILE_READ_UCS_LEVEL <= COMPILE_WRITE_UCS_LEVEL");
    _dst_t *writer;
    if (is_in_obj) {
        RETURN_ON_UNLIKELY_ERR(!unicode_buffer_reserve(writer_addr, unicode_buffer_info, 3 + 6 * len + TAIL_PADDING));
        writer = *writer_addr;
    } else {
        RETURN_ON_UNLIKELY_ERR(!unicode_buffer_reserve(writer_addr, unicode_buffer_info, get_indent_char_count(cur_nested_depth, COMPILE_INDENT_LEVEL) + 3 + 6 * len + TAIL_PADDING));
        writer = *writer_addr;
        write_unicode_indent(&writer, cur_nested_depth);
    }
    *writer++ = '"';
    encode_unicode_impl_no_key(&writer, str_data, len);
    *writer++ = '"';
    *writer++ = ',';
    *writer_addr = writer;
    assert(check_unicode_writer_valid(writer, unicode_buffer_info));
    return true;
}

#include "compile_context/sirw_out.inl.h"
