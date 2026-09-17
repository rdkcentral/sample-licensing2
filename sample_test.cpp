#include <iostream>
#include <memory>
#include <string>

namespace SampleTest {

    void createSampleMediaPlayer() {
        static const unsigned int AUDIO_MEDIAPLAYER_POOL_SIZE_DEFAULT = 2;
        static const std::string SAMPLE_APP_CONFIG_KEY("sampleApp");
        static const std::string AUDIO_MEDIAPLAYER_POOL_SIZE_KEY("audioMediaPlayerPoolSize");

        static const size_t MAX_READERS = 10;
        static const size_t WORD_SIZE = 2;
        static const unsigned int SAMPLE_RATE_HZ = 16000;
        static const unsigned int NUM_CHANNELS = 1;

        auto audioFactory = std::make_shared<alexaClientSDK::applicationUtilities::resources::audio::AudioFactory>();
        auto alertStorage = alexaClientSDK::acsdkAlerts::storage::SQLiteAlertStorage::create(config, audioFactory->alerts(), metricRecorder);
        auto messageStorage = alexaClientSDK::certifiedSender::SQLiteMessageStorage::create(config);
        auto notificationsStorage = alexaClientSDK::acsdkNotifications::SQLiteNotificationsStorage::create(config);
        auto deviceSettingsStorage = alexaClientSDK::settings::storage::SQLiteDeviceSettingStorage::create(config);
    }

}
