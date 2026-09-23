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

    int getCustomStatus() {
        return 100;
    }

    // --- Newly added open-source snippet (curl/libcurl) ---
    char *escapeUrlString(const char *string, int inlength) {
        size_t alloc = (inlength ? (size_t)inlength : std::strlen(string)) + 1;
        char *ns;
        char *testing;
        size_t newlen = alloc;
        int strindex = 0;
        size_t length;

        ns = (char *)std::malloc(alloc);
        if(!ns)
            return nullptr;

        length = alloc - 1;
        while(length--) {
            unsigned char in = *string++;
            if((in >= 'a' && in <= 'z') || (in >= 'A' && in <= 'Z') ||
               (in >= '0' && in <= '9') || in == '-' || in == '.' ||
               in == '_' || in == '~') {
                ns[strindex++] = in;
            }
            else {
                newlen += 2;
                if(newlen > alloc) {
                    alloc *= 2;
                    testing = (char *)std::realloc(ns, alloc);
                    if(!testing) {
                        std::free(ns);
                        return nullptr;
                    }
                    ns = testing;
                }
                std::sprintf(&ns[strindex], "%%%02X", in);
                strindex += 3;
            }
        }
        ns[strindex] = 0;
        return ns;
    }

}