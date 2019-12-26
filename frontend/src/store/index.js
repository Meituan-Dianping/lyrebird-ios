import Vue from 'vue'
import Vuex from 'vuex'
import * as api from '@/api'
import { bus } from '@/eventbus'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    devices: {},
    focusDeviceId: null,
    deviceInfo: {},
    isTakingScreen: false,
    screenShotUrl: null,
    packages: [],
    focusPackageName: null,
    packageInfo: {},
    isLoadingPackageInfo: false,
    isStartingApp: false
  },
  mutations: {
    setDevices (state, devices) {
      state.devices = devices
    },
    setFocusDeviceId (state, deviceId) {
      state.focusDeviceId = deviceId
    },
    setDeviceInfo (state, deviceInfo) {
      state.deviceInfo = deviceInfo
    },
    setIsTakingScreen (state, isTakingScreen) {
      state.isTakingScreen = isTakingScreen
    },
    setScreenShotUrl (state, screenShotUrl) {
      state.screenShotUrl = screenShotUrl
    },
    setPackages (state, packages) {
      state.packages = packages
    },
    setFocusPackageName (state, focusPackageName) {
      state.focusPackageName = focusPackageName
    },
    setPackageInfo (state, packageInfo) {
      state.packageInfo = packageInfo
    },
    setIsLoadingPackageInfo (state, isLoadingPackageInfo) {
      state.isLoadingPackageInfo = isLoadingPackageInfo
    },
    setIsStartingApp (state, isStartingApp) {
      state.isStartingApp = isStartingApp
    }
  },
  actions: {
    loadDevices ({ state, commit }) {
      api.getDevices()
        .then(response => {
          commit('setDevices', response.data.device_list)
          if (!state.devices.hasOwnProperty(state.focusDeviceId)) {
            commit('setFocusDeviceId', null)
            commit('setScreenShotUrl', null)
            commit('setDeviceInfo', {})
            commit('setPackages', {})
            commit('setPackageInfo', [])
          }
        })
        .catch(error => {
          bus.$emit('msg.error', 'Load device list error: ' + error.data.message)
        })
    },
    takeScreenShot ({ state, commit }) {
      commit('setIsTakingScreen', true)
      api.getScreenShot(state.focusDeviceId)
        .then(response => {
          commit('setScreenShotUrl', response.data.imgUrl)
          commit('setIsTakingScreen', false)
        })
        .catch(error => {
          bus.$emit('msg.error', 'Take screenshot error: ' + error.data.message)
        })
    },
    loadPackages ({ state, commit, dispatch }) {
      api.getPackages(state.focusDeviceId)
        .then(response => {
          commit('setPackages', response.data.app_list)
          dispatch('loadDefaultPackageName')
        })
        .catch(error => {
          bus.$emit('msg.error', 'Load device application list error: ' + error.data.message)
        })
    },
    loadDefaultPackageName ({ state, commit, dispatch }) {
      api.getPackageName()
        .then(response => {
          if (response.data.bundle_id) {
            state.packages.find(app => {
              if (app.bundle_id === response.data.bundle_id) {
                commit('setFocusPackageName', response.data.bundle_id)
                dispatch('loadPackageInfo')
              }
            })
          }
        })
        .catch(error => {
          bus.$emit('msg.error', 'Load default application error: ' + error.data.message)
        })
    },
    loadPackageInfo ({ state, commit }) {
      console.log('loadPackageInfo')
      commit('setIsLoadingPackageInfo', true)
      api.getAppInfo(state.focusDeviceId, state.focusPackageName)
        .then(response => {
          commit('setPackageInfo', response.data.app_info)
          commit('setIsLoadingPackageInfo', false)
        })
        .catch(error => {
          bus.$emit('msg.error', 'Load application information error: ' + error.data.message)
        })
    },
    startApp ({ state, commit }) {
      commit('setIsStartingApp', true)
      api.startApp(state.focusDeviceId, state.focusPackageName)
        .then(
          commit('setIsStartingApp', false)
        )
        .catch(error => {
          bus.$emit('msg.error', 'Start application' + state.focusPackageName + ' error: ' + error.data.message)
        })
    },
    stopApp ({ state }) {
      api.stopApp(state.focusDeviceId, state.focusPackageName)
      .catch(error => {
        bus.$emit('msg.error', 'Stop application' + state.focusPackageName + ' error: ' + error.data.message)
      })
    }
  }
})
