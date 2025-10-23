#pragma once
#include <dftracer/core/common/logging.h>
#include <dftracer/core/common/singleton.h>
#include <dftracer/core/utils/configuration_manager.h>

#include <cstdio>
#include <cstring>
#include <stdexcept>
namespace dftracer {
class STDIOWriter {
 public:
  STDIOWriter() : max_size_(0), fh_(nullptr) {}
  void initialize(const char* filename) {
    this->filename = filename;
    auto conf =
        dftracer::Singleton<dftracer::ConfigurationManager>::get_instance();
    max_size_ = conf->write_buffer_size;
    fh_ = fopen(filename, "ab+");
    if (fh_ == nullptr) {
      DFTRACER_LOG_ERROR("unable to create log file %s: errno=%d (%s)",
                         filename, errno, strerror(errno));  // GCOVR_EXCL_LINE
    } else {
      setvbuf(fh_, NULL, _IOLBF, max_size_ + 16 * 1024);
      DFTRACER_LOG_INFO("created log file %s", filename);
    }
  }

  ~STDIOWriter() {}
  void finalize(int index) {
    if (fh_ != nullptr) {
      DFTRACER_LOG_INFO("Finalizing STDIOWriter", "");
      fflush(fh_);
      long file_size = 0;
      if (fh_ != nullptr) {
        fseek(fh_, 0, SEEK_END);
        file_size = ftell(fh_);
        fseek(fh_, 0, SEEK_SET);
      }
      int status = fclose(fh_);
      if ((index < 5 || file_size == 0) && filename != nullptr) {
        unlink(filename);
      }
      if (status != 0) {
        DFTRACER_LOG_ERROR("unable to close log file %s",
                           this->filename);  // GCOVR_EXCL_LINE
      }
      fh_ = nullptr;
    }
  }

  // Write data to buffer, flush if necessary
  size_t write(const char* data, size_t len, bool force = false) {
    if (fh_ != nullptr && (force || len >= max_size_)) {
      // Use stdio file locking (flockfile/funlockfile) for FILE*
      // needed for fork and spawn cases to maintain consistency
      // Note this may not work with nfs and should typically either create a
      // new file per fork or use a local filesystem which supports flockfile.
      flockfile(fh_);
      auto written = std::fwrite(data, 1, len, fh_);
      funlockfile(fh_);
      if (written != len) {
        DFTRACER_LOG_ERROR("unable to write log file %s",
                           this->filename);  // GCOVR_EXCL_LINE
      }
    }
    return len;
  }

 private:
  const char* filename;
  size_t max_size_;
  FILE* fh_;
};
}  // namespace dftracer