#include <vector>
#include <string.h>
#include <jni.h>
#include <android/log.h>
#include <gstreamer-1.0/gst/gst.h>

/*
 * Java Bindings
 */
static jstring
gst_native_get_gstreamer_info(JNIEnv *env, jobject thiz) {
    char *version_utf8 = gst_version_string();
    jstring version_jstring = env->NewStringUTF(version_utf8);
    g_free(version_utf8);
    return version_jstring;
}

static std::vector<JNINativeMethod> native_methods = {
        {"nativeGetGStreamerInfo", "()Ljava/lang/String;", (void *) gst_native_get_gstreamer_info}
};

jint JNI_OnLoad(JavaVM *vm, void *reserved) {
    JNIEnv *env = NULL;

    if (vm->GetEnv((void **) &env, JNI_VERSION_1_4) != JNI_OK) {
        __android_log_print(ANDROID_LOG_ERROR, "GStreamer+JNI", "Could not retrieve JNIEnv");
        return 0;
    }
    jclass klass = env->FindClass("cn/huww98/picontroller/Gstreamer");
    env->RegisterNatives(klass, native_methods.data(), (jint) native_methods.size());

    return JNI_VERSION_1_4;
}
