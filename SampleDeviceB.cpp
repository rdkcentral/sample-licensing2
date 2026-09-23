#include <iostream>
#include <memory>
#include <string>
#include <vector>

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

    bool testAVSInit() {
        auto builder = avsCommon::avs::initialization::InitializationParametersBuilder::create();
        if (!builder) {
            return false;
        }

        builder->withJsonStreams(configJsonStreams);

        auto initParams = builder->build();
        if (!initParams) {
            return false;
        }

        acsdkSampleApplication::SampleApplicationComponent sampleAppComponent =
            acsdkSampleApplication::getComponent(std::move(initParams), m_shutdownRequiredList);

        auto manufactory = acsdkManufactory::Manufactory<
            std::shared_ptr<avsCommon::avs::initialization::AlexaClientSDKInit>,
            std::shared_ptr<avsCommon::sdkInterfaces::AuthDelegateInterface>,
            std::shared_ptr<avsCommon::sdkInterfaces::ContextManagerInterface>,
            std::shared_ptr<avsCommon::sdkInterfaces::LocaleAssetsManagerInterface>,
            std::shared_ptr<avsCommon::utils::DeviceInfo>,
            std::shared_ptr<avsCommon::utils::configuration::ConfigurationNode>,
            std::shared_ptr<avsCommon::utils::metrics::MetricRecorderInterface>,
            std::shared_ptr<registrationManager::CustomerDataManagerInterface>,
            std::shared_ptr<acsdkCryptoInterfaces::CryptoFactoryInterface>,
            std::shared_ptr<acsdkCryptoInterfaces::KeyStoreInterface>,
            std::shared_ptr<sampleApp::UIManager>>::create(sampleAppComponent);

        auto metricRecorder = manufactory->get<std::shared_ptr<avsCommon::utils::metrics::MetricRecorderInterface>>();
        auto m_sdkInit = manufactory->get<std::shared_ptr<avsCommon::avs::initialization::AlexaClientSDKInit>>();
        if (!m_sdkInit) {
            return false;
        }

        auto configPtr = manufactory->get<std::shared_ptr<avsCommon::utils::configuration::ConfigurationNode>>();
        if (!configPtr) {
            return false;
        }

        return true;
    }

}