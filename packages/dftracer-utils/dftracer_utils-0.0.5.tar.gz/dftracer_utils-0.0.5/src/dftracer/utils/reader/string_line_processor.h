#ifndef DFTRACER_UTILS_READER_STRING_LINE_PROCESSOR_H
#define DFTRACER_UTILS_READER_STRING_LINE_PROCESSOR_H

#include <dftracer/utils/reader/line_processor.h>

#include <string>

namespace dftracer::utils {
class StringLineProcessor : public LineProcessor {
   private:
    std::string& result_;

   public:
    explicit StringLineProcessor(std::string& result) : result_(result) {}

    bool process(const char* data, std::size_t length) override {
        result_.append(data, length);
        result_.append(1, '\n');
        return true;
    }

    void begin(std::size_t start_line, std::size_t end_line) override {
        std::size_t estimated_lines = end_line - start_line + 1;
        result_.reserve(estimated_lines * 100);
    }
};

}  // namespace dftracer::utils

#endif  // DFTRACER_UTILS_READER_STRING_LINE_PROCESSOR_H
