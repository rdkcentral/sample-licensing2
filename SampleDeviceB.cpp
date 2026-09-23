#include <iostream>
#include <memory>
#include <string>

namespace SampleTestB {

    void testAudioModuleB() {
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

    bool testMediaPlayersInitialization() {
        auto speakMediaPlayer = alexaClientSDK::mediaPlayer::MediaPlayer::create(
            std::move(speakAudioFactory),
            speakerMediaInterfaces->speaker,
            "SpeakMediaPlayer",
            true);
        if (!speakMediaPlayer) {
            alexaClientSDK::sampleApp::ConsolePrinter::simplePrint("Failed to create speak media player!");
            return false;
        }

        auto alertsMediaPlayer = alexaClientSDK::mediaPlayer::MediaPlayer::create(
            std::move(alertsAudioFactory),
            alertsMediaInterfaces->speaker,
            "AlertsMediaPlayer",
            true);
        if (!alertsMediaPlayer) {
            alexaClientSDK::sampleApp::ConsolePrinter::simplePrint("Failed to create alerts media player!");
            return false;
        }

        auto notificationsMediaPlayer = alexaClientSDK::mediaPlayer::MediaPlayer::create(
            std::move(notificationsAudioFactory),
            notificationMediaInterfaces->speaker,
            "NotificationsMediaPlayer",
            true);
        if (!notificationsMediaPlayer) {
            alexaClientSDK::sampleApp::ConsolePrinter::simplePrint("Failed to create notifications media player!");
            return false;
        }

        auto ringtoneMediaPlayer = alexaClientSDK::mediaPlayer::MediaPlayer::create(
            std::move(ringtoneAudioFactory),
            ringtoneMediaInterfaces->speaker,
            "RingtoneMediaPlayer",
            true);
        if (!ringtoneMediaPlayer) {
            alexaClientSDK::sampleApp::ConsolePrinter::simplePrint("Failed to create ringtone media player!");
            return false;
        }

        return true;
    }

}