#include <iostream>
#include <memory>
#include <string>

namespace SampleTest {

    // 1. Unrelated dummy function above
    void dummyHelperFunction() {
        std::cout << "Unrelated helper function" << std::endl;
    }

    // 2. The snippet cut and pasted into a completely different function context
    void relocatedAudioModule() {
        std::shared_ptr<alexaClientSDK::defaultClient::DefaultClient> client = alexaClientSDK::defaultClient::DefaultClient::create(
            deviceInfo,
            customerDataManager,
            m_externalMusicProviderMediaPlayersMap,
            m_externalMusicProviderSpeakersMap,
            m_adapterToCreateFuncMap,
            m_speakMediaPlayer,
            std::move(audioMediaPlayerFactory),
            m_alertsMediaPlayer,
            m_notificationsMediaPlayer,
            m_bluetoothMediaPlayer,
            m_ringtoneMediaPlayer,
            m_systemSoundMediaPlayer,
            speakerMediaInterfaces->speaker,
            audioSpeakers,
            alertsMediaInterfaces->speaker,
            notificationMediaInterfaces->speaker,
            bluetoothMediaInterfaces->speaker,
            ringtoneMediaInterfaces->speaker,
            systemSoundMediaInterfaces->speaker,
            {},
            nullptr,
            audioFactory,
            authDelegate,
            std::move(alertStorage),
            std::move(messageStorage),
            std::move(notificationsStorage),
            std::move(deviceSettingsStorage),
            nullptr,
            miscStorage,
            { userInterfaceManager },
            { userInterfaceManager },
            std::move(internetConnectionMonitor),
            displayCardsSupported,
            m_capabilitiesDelegate,
            contextManager,
            transportFactory,
            avsGatewayManager,
            localeAssetsManager,
            {},
            nullptr,
            firmwareVersion,
            true,
            nullptr,
            nullptr,
            metricRecorder,
            nullptr,
            nullptr,
            std::make_shared<alexaClientSDK::sampleApp::ExternalCapabilitiesBuilder>(deviceInfo),
            std::make_shared<alexaClientSDK::capabilityAgents::speakerManager::DefaultChannelVolumeFactory>(),
            true,
            std::make_shared<alexaClientSDK::acl::MessageRouterFactory>(),
            nullptr,
            tapToTalkAudioProvider);
    }

}