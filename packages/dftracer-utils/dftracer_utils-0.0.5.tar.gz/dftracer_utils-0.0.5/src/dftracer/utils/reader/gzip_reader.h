#ifndef DFTRACER_UTILS_READER_GZIP_READER_H
#define DFTRACER_UTILS_READER_GZIP_READER_H

#include <dftracer/utils/indexer/indexer.h>
#include <dftracer/utils/reader/line_processor.h>
#include <dftracer/utils/reader/reader.h>
#include <dftracer/utils/reader/streams/gzip_byte_stream.h>
#include <dftracer/utils/reader/streams/gzip_factory.h>
#include <dftracer/utils/reader/streams/gzip_line_byte_stream.h>

#include <cstddef>
#include <memory>
#include <string>

namespace dftracer::utils {
class GzipReader : public Reader {
   public:
    GzipReader(const std::string &gz_path, const std::string &idx_path,
               std::size_t index_ckpt_size = Indexer::DEFAULT_CHECKPOINT_SIZE);
    explicit GzipReader(Indexer *indexer);
    ~GzipReader();

    // Disable copy constructor and copy assignment
    GzipReader(const GzipReader &) = delete;
    GzipReader &operator=(const GzipReader &) = delete;
    GzipReader(GzipReader &&other) noexcept;
    GzipReader &operator=(GzipReader &&other) noexcept;

    // Reader interface implementation
    std::size_t get_max_bytes() const override;
    std::size_t get_num_lines() const override;
    const std::string &get_archive_path() const override;
    const std::string &get_idx_path() const override;
    void set_buffer_size(std::size_t size) override;

    std::size_t read(std::size_t start_bytes, std::size_t end_bytes,
                     char *buffer, std::size_t buffer_size) override;
    std::size_t read_line_bytes(std::size_t start_bytes, std::size_t end_bytes,
                                char *buffer, std::size_t buffer_size) override;
    std::string read_lines(std::size_t start, std::size_t end) override;
    void read_lines_with_processor(std::size_t start, std::size_t end,
                                   LineProcessor &processor) override;
    void read_line_bytes_with_processor(std::size_t start_bytes,
                                        std::size_t end_bytes,
                                        LineProcessor &processor) override;

    void reset() override;
    bool is_valid() const override;
    std::string get_format_name() const override;

   private:
    std::string gz_path;
    std::string idx_path;
    bool is_open;
    std::size_t default_buffer_size;
    std::unique_ptr<Indexer>
        owned_indexer;     // Only used when we create the indexer
    Indexer *indexer_ptr;  // Non-owning pointer to indexer (could be owned or
                           // external)
    std::unique_ptr<GzipStreamFactory> stream_factory;
    std::unique_ptr<GzipByteStream> byte_stream;
    std::unique_ptr<GzipLineByteStream> line_byte_stream;

    // Helper method for line processing
    std::size_t process_lines(const char *buffer_data, std::size_t buffer_size,
                              std::size_t &current_line, std::size_t start_line,
                              std::size_t end_line,
                              std::string &line_accumulator,
                              LineProcessor &processor);
};

}  // namespace dftracer::utils

#endif  // DFTRACER_UTILS_READER_GZIP_READER_H
