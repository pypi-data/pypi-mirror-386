#include <dftracer/utils/common/logging.h>
#include <dftracer/utils/reader/reader.h>
#include <dftracer/utils/reader/reader_factory.h>

#include <cstring>

using namespace dftracer::utils;

static Reader *cast_reader(dft_reader_handle_t reader) {
    return static_cast<Reader *>(reader);
}

extern "C" {

// Helper functions for C API
static int validate_handle(dft_reader_handle_t reader) {
    return reader ? 0 : -1;
}

dft_reader_handle_t dft_reader_create(const char *gz_path, const char *idx_path,
                                      size_t index_ckpt_size) {
    if (!gz_path || !idx_path) {
        DFTRACER_UTILS_LOG_ERROR("Both gz_path and idx_path cannot be null",
                                 "");
        return nullptr;
    }

    try {
        auto reader = ReaderFactory::create(gz_path, idx_path, index_ckpt_size);
        return static_cast<dft_reader_handle_t>(reader.release());
    } catch (const std::exception &e) {
        DFTRACER_UTILS_LOG_ERROR("Failed to create DFT reader: %s", e.what());
        return nullptr;
    }
}

dft_reader_handle_t dft_reader_create_with_indexer(
    dft_indexer_handle_t indexer) {
    if (!indexer) {
        DFTRACER_UTILS_LOG_ERROR("Indexer cannot be null", "");
        return nullptr;
    }

    DFTRACER_UTILS_LOG_DEBUG("Creating DFT reader with provided indexer", "");

    try {
        auto reader = ReaderFactory::create(static_cast<Indexer *>(indexer));
        return static_cast<dft_reader_handle_t>(reader.release());
    } catch (const std::exception &e) {
        DFTRACER_UTILS_LOG_ERROR("Failed to create DFT reader with indexer: %s",
                                 e.what());
        return nullptr;
    }
}

void dft_reader_destroy(dft_reader_handle_t reader) {
    if (reader) {
        delete cast_reader(reader);
    }
}

int dft_reader_get_max_bytes(dft_reader_handle_t reader, size_t *max_bytes) {
    if (validate_handle(reader) || !max_bytes) {
        return -1;
    }

    try {
        *max_bytes = cast_reader(reader)->get_max_bytes();
        return 0;
    } catch (const std::exception &e) {
        DFTRACER_UTILS_LOG_ERROR("Failed to get max bytes: %s", e.what());
        return -1;
    }
}

int dft_reader_get_num_lines(dft_reader_handle_t reader, size_t *num_lines) {
    if (validate_handle(reader) || !num_lines) {
        return -1;
    }

    try {
        *num_lines = cast_reader(reader)->get_num_lines();
        return 0;
    } catch (const std::exception &e) {
        DFTRACER_UTILS_LOG_ERROR("Failed to get number of lines: %s", e.what());
        return -1;
    }
}

int dft_reader_read(dft_reader_handle_t reader, size_t start_bytes,
                    size_t end_bytes, char *buffer, size_t buffer_size) {
    if (validate_handle(reader) || !buffer || buffer_size == 0) {
        return -1;
    }

    try {
        size_t bytes_read = cast_reader(reader)->read(start_bytes, end_bytes,
                                                      buffer, buffer_size);
        return static_cast<int>(bytes_read);
    } catch (const std::exception &e) {
        DFTRACER_UTILS_LOG_ERROR("Failed to read: %s", e.what());
        return -1;
    }
}

int dft_reader_read_line_bytes(dft_reader_handle_t reader, size_t start_bytes,
                               size_t end_bytes, char *buffer,
                               size_t buffer_size) {
    if (validate_handle(reader) || !buffer || buffer_size == 0) {
        return -1;
    }

    try {
        size_t bytes_read = cast_reader(reader)->read_line_bytes(
            start_bytes, end_bytes, buffer, buffer_size);
        return static_cast<int>(bytes_read);
    } catch (const std::exception &e) {
        DFTRACER_UTILS_LOG_ERROR("Failed to read line bytes: %s", e.what());
        return -1;
    }
}

int dft_reader_read_lines(dft_reader_handle_t reader, size_t start_line,
                          size_t end_line, char *buffer, size_t buffer_size,
                          size_t *bytes_written) {
    if (validate_handle(reader) || !buffer || buffer_size == 0 ||
        !bytes_written) {
        return -1;
    }

    try {
        std::string result =
            cast_reader(reader)->read_lines(start_line, end_line);

        size_t result_size = result.size();
        if (result_size >= buffer_size) {
            *bytes_written = result_size;
            return -1;
        }

        std::memcpy(buffer, result.c_str(), result_size);
        buffer[result_size] = '\0';
        *bytes_written = result_size;

        return 0;
    } catch (const std::exception &e) {
        DFTRACER_UTILS_LOG_ERROR("Failed to read lines: %s", e.what());
        *bytes_written = 0;
        return -1;
    }
}

void dft_reader_reset(dft_reader_handle_t reader) {
    if (reader) {
        cast_reader(reader)->reset();
    }
}

}  // extern "C"
