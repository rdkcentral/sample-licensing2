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

}

// ============================================================================
// LINUX KERNEL RED-BLACK TREE IMPLEMENTATION (GPL-2.0)
// Source: kernel/lib/rbtree.c
// ============================================================================

struct rb_node {
    unsigned long  __rb_parent_color;
    struct rb_node *rb_right;
    struct rb_node *rb_left;
} __attribute__((aligned(sizeof(long))));

struct rb_root {
    struct rb_node *rb_node;
};

#define RB_RED      0
#define RB_BLACK    1

#define rb_parent(r)   ((struct rb_node *)((r)->__rb_parent_color & ~3))

static void __rb_rotate_left(struct rb_node *node, struct rb_root *root) {
    struct rb_node *right = node->rb_right;
    struct rb_node *parent = rb_parent(node);

    if ((node->rb_right = right->rb_left))
        right->rb_left->__rb_parent_color = (unsigned long)node | (right->rb_left->__rb_parent_color & 1);
    right->rb_left = node;

    right->__rb_parent_color = (unsigned long)parent | (right->__rb_parent_color & 1);

    if (parent) {
        if (node == parent->rb_left)
            parent->rb_left = right;
        else
            parent->rb_right = right;
    } else
        root->rb_node = right;
    node->__rb_parent_color = (unsigned long)right | (node->__rb_parent_color & 1);
}

static void __rb_rotate_right(struct rb_node *node, struct rb_root *root) {
    struct rb_node *left = node->rb_left;
    struct rb_node *parent = rb_parent(node);

    if ((node->rb_left = left->rb_right))
        left->rb_right->__rb_parent_color = (unsigned long)node | (left->rb_right->__rb_parent_color & 1);
    left->rb_right = node;

    left->__rb_parent_color = (unsigned long)parent | (left->__rb_parent_color & 1);

    if (parent) {
        if (node == parent->rb_right)
            parent->rb_right = left;
        else
            parent->rb_left = left;
    } else
        root->rb_node = left;
    node->__rb_parent_color = (unsigned long)left | (node->__rb_parent_color & 1);
}

void rb_insert_color(struct rb_node *node, struct rb_root *root) {
    struct rb_node *parent, *gparent;

    while ((parent = rb_parent(node)) && (parent->__rb_parent_color & 1) == RB_RED) {
        gparent = rb_parent(parent);

        if (parent == gparent->rb_left) {
            {
                register struct rb_node *uncle = gparent->rb_right;
                if (uncle && (uncle->__rb_parent_color & 1) == RB_RED) {
                    uncle->__rb_parent_color = (unsigned long)rb_parent(uncle) | RB_BLACK;
                    parent->__rb_parent_color = (unsigned long)gparent | RB_BLACK;
                    gparent->__rb_parent_color = (unsigned long)rb_parent(gparent) | RB_RED;
                    node = gparent;
                    continue;
                }
            }

            if (parent->rb_right == node) {
                register struct rb_node *tmp;
                __rb_rotate_left(parent, root);
                tmp = parent;
                parent = node;
                node = tmp;
            }

            parent->__rb_parent_color = (unsigned long)gparent | RB_BLACK;
            gparent->__rb_parent_color = (unsigned long)rb_parent(gparent) | RB_RED;
            __rb_rotate_right(gparent, root);
        } else {
            {
                register struct rb_node *uncle = gparent->rb_left;
                if (uncle && (uncle->__rb_parent_color & 1) == RB_RED) {
                    uncle->__rb_parent_color = (unsigned long)rb_parent(uncle) | RB_BLACK;
                    parent->__rb_parent_color = (unsigned long)gparent | RB_BLACK;
                    gparent->__rb_parent_color = (unsigned long)rb_parent(gparent) | RB_RED;
                    node = gparent;
                    continue;
                }
            }

            if (parent->rb_left == node) {
                register struct rb_node *tmp;
                __rb_rotate_right(parent, root);
                tmp = parent;
                parent = node;
                node = tmp;
            }

            parent->__rb_parent_color = (unsigned long)gparent | RB_BLACK;
            gparent->__rb_parent_color = (unsigned long)rb_parent(gparent) | RB_RED;
            __rb_rotate_left(gparent, root);
        }
    }

    root->rb_node->__rb_parent_color = (unsigned long)rb_parent(root->rb_node) | RB_BLACK;
}