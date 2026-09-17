#include <iostream>
#include <memory>
#include <string>

namespace SampleTest {
    void configureAudioStream() {
        static const size_t MAX_READERS = 10;
        static const size_t WORD_SIZE = 2;
        static const unsigned int SAMPLE_RATE_HZ = 16000;
        static const unsigned int NUM_CHANNELS = 1;
        std::cout << "Audio Stream Configured" << std::endl;
    }
}
