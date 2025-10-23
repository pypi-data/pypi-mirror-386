#ifndef DFTRACER_UTILS_PIPELINE_TASKS_TYPED_TASK_H
#define DFTRACER_UTILS_PIPELINE_TASKS_TYPED_TASK_H

#include <dftracer/utils/common/logging.h>
#include <dftracer/utils/pipeline/tasks/task.h>

#include <typeindex>

namespace dftracer::utils {

template <typename I, typename O>
class TypedTask : public Task {
   protected:
    TypedTask() : Task(typeid(I), typeid(O)) {}

   public:
    virtual ~TypedTask() = default;

    I get_input(std::any& in) { return std::any_cast<I>(in); }

    O get_output(std::any& out) { return std::any_cast<O>(out); }

    virtual O apply(I in) = 0;

   protected:
    bool validate(I in) {
        bool result = std::type_index(typeid(in)) == this->get_input_type();
        if (!result) {
            DFTRACER_UTILS_LOG_ERROR(
                "Input type validation failed, expected: {}, got: {}",
                this->get_input_type().name(), typeid(in).name());
        }
        return result;
    }

   public:
    std::any execute(std::any& in) override final {
        return apply(std::any_cast<I>(in));
    }
};

}  // namespace dftracer::utils

#endif  // DFTRACER_UTILS_PIPELINE_TASKS_TYPED_TASK_H
