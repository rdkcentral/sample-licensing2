#include <iostream>
#include <memory>
#include <string>
#include <cstdlib>
#include <cstring>

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
}

// --- ADDED IN PR: SQLite Memory Allocation Engine (Public Domain / SQLite) ---
extern "C" {

struct Mem0Global {
    int NumberType;
    int bMemstat;
    int bCoreMutex;
    void *pScratch;
    int szScratch;
    int nScratch;
    void *pPage;
    int szPage;
    int nPage;
    int mxParserStack;
} sqlite3Mem0;

void *sqlite3MemMalloc(int nByte) {
    struct {
        int totalSize;
        int dummy;
    } *pPrior;
    int nByte2;
    void *p = 0;

    if (nByte > 0) {
        nByte2 = (nByte + 7) & ~7;
        pPrior = (decltype(pPrior))malloc(nByte2 + 8);
        if (pPrior) {
            pPrior->totalSize = nByte2;
            p = (void *)&pPrior[1];
        }
    }
    return p;
}

void sqlite3MemFree(void *pPrior) {
    struct {
        int totalSize;
        int dummy;
    } *pReal;
    if (pPrior) {
        pReal = (decltype(pReal))pPrior;
        pReal--;
        free(pReal);
    }
}

void *sqlite3MemRealloc(void *pPrior, int nByte) {
    struct {
        int totalSize;
        int dummy;
    } *pOld;
    void *pNew = 0;
    if (pPrior == 0) {
        return sqlite3MemMalloc(nByte);
    }
    if (nByte <= 0) {
        sqlite3MemFree(pPrior);
        return 0;
    }
    pOld = (decltype(pOld))pPrior;
    pOld--;
    pNew = sqlite3MemMalloc(nByte);
    if (pNew) {
        memcpy(pNew, pPrior, pOld->totalSize < nByte ? pOld->totalSize : nByte);
        sqlite3MemFree(pPrior);
    }
    return pNew;
}

}