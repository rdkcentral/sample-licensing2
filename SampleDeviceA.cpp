#include <iostream>
#include <memory>
#include <string>

namespace SampleTestC {

    void testAudioModuleC() {
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
            false,
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

    // Custom non-open-source function added in this PR
    int getCustomDeviceStatus() {
        int statusReady = 1;
        return statusReady;
    }

    bool initializeSampleApplication(
    std::shared_ptr<alexaClientSDK::sampleApp::ConsoleReader> reader,
    const std::vector<std::string>& configFiles,
    const std::string& pathToInputFolder,
    const std::string& logLevel) {

    alexaClientSDK::avsCommon::utils::logger::Level logLevelValue =
        alexaClientSDK::avsCommon::utils::logger::Level::UNKNOWN;
    if (!logLevel.empty()) {
        logLevelValue = alexaClientSDK::avsCommon::utils::logger::convertStringToLogLevel(logLevel);
        if (alexaClientSDK::avsCommon::utils::logger::Level::UNKNOWN == logLevelValue) {
            alexaClientSDK::sampleApp::ConsolePrinter::simplePrint("Unknown log level: " + logLevel);
            return false;
        }
    }

    if (configFiles.empty()) {
        alexaClientSDK::sampleApp::ConsolePrinter::simplePrint("Config file(s) not specified!");
        return false;
    }

    std::vector<std::shared_ptr<std::istream>> configStreamList;
    for (auto configFile : configFiles) {
        if (configFile.empty()) {
            alexaClientSDK::sampleApp::ConsolePrinter::simplePrint("Config file not specified!");
            return false;
        }
        auto configStream = std::shared_ptr<std::ifstream>(new std::ifstream(configFile));
        if (!configStream->good()) {
            alexaClientSDK::sampleApp::ConsolePrinter::simplePrint("Failed to read config file " + configFile);
            return false;
        }
        configStreamList.push_back(configStream);
    }

    auto configurationNode = alexaClientSDK::avsCommon::utils::configuration::ConfigurationNode::create(configStreamList);
    if (!configurationNode) {
        alexaClientSDK::sampleApp::ConsolePrinter::simplePrint("Failed to create a valid configuration node!");
        return false;
    }

    return true;
}

}
